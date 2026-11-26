"""
updater.py — Verificação e aplicação de atualizações automáticas.

Consulta a release mais recente do GitHub, compara com version.py local.
Se houver nova versão: baixa o novo .exe e aplica via script .bat após fechar.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from version import REPOSITORY, VERSION

GITHUB_API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"


def _versao_para_tupla(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def buscar_release_mais_recente(timeout: int = 6) -> dict:
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"User-Agent": f"EnviarAssinaturas-Updater/{VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}


def verificar_atualizacao() -> dict:
    local = VERSION
    release = buscar_release_mais_recente()

    if not release:
        return {"disponivel": False, "versao_local": local,
                "versao_nova": "", "url_download": "", "notas": ""}

    remota = release.get("tag_name", "0.0.0").lstrip("v")
    notas = release.get("body", "")

    url_exe = ""
    for asset in release.get("assets", []):
        nome = asset.get("name", "").lower()
        url = asset.get("browser_download_url", "")
        if nome.endswith(".exe") and not url_exe:
            url_exe = url

    versao_mais_nova = bool(remota) and (
        _versao_para_tupla(remota) > _versao_para_tupla(local)
    )
    disponivel = bool(url_exe) and versao_mais_nova

    return {
        "disponivel": disponivel,
        "versao_mais_nova": versao_mais_nova,
        "versao_local": local,
        "versao_nova": remota,
        "url_download": url_exe,
        "notas": notas,
    }


def _baixar_arquivo(url: str, destino: str, callback=None):
    req = urllib.request.Request(
        url, headers={"User-Agent": f"EnviarAssinaturas-Updater/{VERSION}"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        baixados = 0
        with open(destino, "wb") as f:
            while True:
                bloco = resp.read(65536)
                if not bloco:
                    break
                f.write(bloco)
                baixados += len(bloco)
                if callback:
                    callback(baixados, total)


def baixar_atualizacao(url_download: str, callback_progresso=None) -> str | None:
    """Baixa o novo .exe ao lado do atual, sem aplicar. None fora do executável."""
    if not getattr(sys, "frozen", False):
        return None
    nome_arq = url_download.split("/")[-1].split("?")[0]
    with tempfile.TemporaryDirectory() as tmp:
        caminho_tmp = os.path.join(tmp, nome_arq)
        _baixar_arquivo(url_download, caminho_tmp, callback_progresso)
        novo = sys.executable + ".new"
        shutil.copy2(caminho_tmp, novo)
    return novo


def _script_troca(novo: str, atual: str) -> str:
    # Repete o move: o programa pode levar alguns segundos para fechar o Chrome
    return "\n".join([
        "@echo off",
        "set PYINSTALLER_RESET_ENVIRONMENT=1",
        "set /a n=0",
        ":tentar",
        "ping -n 2 127.0.0.1 >nul",
        f'move /y "{novo}" "{atual}" >nul 2>&1 && goto abrir',
        "set /a n+=1",
        "if %n% lss 60 goto tentar",
        ":abrir",
        f'start "" "{atual}"',
        'del "%~f0"',
        "",
    ])


def instalar_atualizacao(novo_exe: str) -> None:
    """Agenda a troca do .exe; o programa deve fechar logo em seguida."""
    atual = sys.executable
    bat = Path(atual).parent / "_update_replace.bat"
    bat.write_text(_script_troca(novo_exe, atual), encoding="mbcs")
    subprocess.Popen(["cmd", "/c", str(bat)], shell=False,
                     creationflags=subprocess.CREATE_NO_WINDOW)


def reiniciar():
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)
