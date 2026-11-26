"""
Controle dos processos abertos pela automação (Windows).

O chromedriver entra em um Job Object; o Chrome e todos os subprocessos criados
por ele herdam o job. Assim é possível encerrar exatamente os processos da
automação, sem tocar no Chrome que o usuário abriu. Se o próprio programa for
morto ou travar, o Windows encerra o job sozinho.
"""
import ctypes
import logging
import os
import subprocess
import sys
import threading
from ctypes import wintypes

logger = logging.getLogger(__name__)

encerrando = threading.Event()  # ligado quando o usuário fecha o programa
_lock = threading.Lock()
_job = None
_trava = None

_KILL_ON_JOB_CLOSE = 0x2000
_INFO_LIMITE_ESTENDIDO = 9
_PROCESS_TERMINATE_E_SET_QUOTA = 0x0001 | 0x0100


class _LimiteBasico(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _LimiteEstendido(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _LimiteBasico), ("IoInfo", ctypes.c_uint64 * 6),
        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _kernel32():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    return k


def _obter_job(k):
    global _job
    if _job:
        return _job
    job = k.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    info = _LimiteEstendido()
    info.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE
    if not k.SetInformationJobObject(job, _INFO_LIMITE_ESTENDIDO, ctypes.byref(info), ctypes.sizeof(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    _job = job
    return job


def registrar(pid: int) -> None:
    """Coloca o processo (e tudo que ele vier a criar) sob controle da automação."""
    with _lock:
        if encerrando.is_set():
            raise RuntimeError("Automação encerrada pelo usuário.")
        if sys.platform != "win32":
            return
        try:
            k = _kernel32()
            job = _obter_job(k)
            processo = k.OpenProcess(_PROCESS_TERMINATE_E_SET_QUOTA, False, pid)
            if not processo:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                if not k.AssignProcessToJobObject(job, processo):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                k.CloseHandle(processo)
        except OSError:
            logger.warning("Não foi possível vincular o processo %s ao job", pid, exc_info=True)


def encerrar_tudo() -> None:
    """Mata imediatamente todos os processos registrados que ainda existirem."""
    with _lock:
        if _job:
            _kernel32().TerminateJobObject(_job, 1)


def travar_instancia(caminho) -> bool:
    """
    Garante uma única janela usando o perfil e o diário desta pasta. A trava vale
    até o processo terminar (o Windows a libera mesmo se ele for morto).
    """
    global _trava
    if _trava or sys.platform != "win32":
        return True
    import msvcrt

    arquivo = open(caminho, "a")
    try:
        arquivo.seek(0)
        msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        arquivo.close()
        return False
    _trava = arquivo
    return True


# Órfão = Chrome do perfil da automação cujo chromedriver, ou o programa que o
# abriu, já não existe. Quem ainda tem dono vivo não é tocado.
_SCRIPT_ORFAOS = r"""
$perfil = $env:PERFIL_AUTOMACAO
$todos = @(Get-CimInstance Win32_Process)
$porId = @{}
foreach ($p in $todos) { $porId[[int]$p.ProcessId] = $p }
function Obter-Pai($p) {
    $x = $porId[[int]$p.ParentProcessId]
    if ($x -and $x.CreationDate -le $p.CreationDate) { $x }
}
$matar = @{}
foreach ($p in $todos) {
    if ($p.Name -ne 'chrome.exe' -or -not $p.CommandLine) { continue }
    if ($p.CommandLine.IndexOf($perfil, [StringComparison]::OrdinalIgnoreCase) -lt 0) { continue }
    $raiz = $p
    while (($pai = Obter-Pai $raiz) -and $pai.Name -eq 'chrome.exe') { $raiz = $pai }
    $driver = Obter-Pai $raiz
    if ($driver -and $driver.Name -eq 'chromedriver.exe') {
        if (Obter-Pai $driver) { continue }
        $matar[[int]$driver.ProcessId] = 1
    }
    $matar[[int]$p.ProcessId] = 1
}
foreach ($id in $matar.Keys) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
"""


def encerrar_orfaos(perfil) -> None:
    """Encerra Chrome deixado para trás (ex.: versão antiga) usando este perfil."""
    if sys.platform != "win32":
        return
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _SCRIPT_ORFAOS],
            env={**os.environ, "PERFIL_AUTOMACAO": str(perfil)},
            capture_output=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        logger.warning("Não foi possível procurar processos órfãos", exc_info=True)
