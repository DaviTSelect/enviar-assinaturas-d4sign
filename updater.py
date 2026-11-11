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


def aplicar_atualizacao(url_download: str, versao_nova: str,
                         callback_progresso=None) -> bool:
    nome_arq = url_download.split("/")[-1].split("?")[0]
    with tempfile.TemporaryDirectory() as tmp:
        caminho_tmp = os.path.join(tmp, nome_arq)
        _baixar_arquivo(url_download, caminho_tmp, callback_progresso)
        _aplicar_exe(caminho_tmp)
    return True


def _aplicar_exe(caminho_novo_exe: str):
    exe_atual = sys.executable if getattr(sys, "frozen", False) else None
    if not exe_atual:
        return

    novo_exe_copia = exe_atual + ".new"
    shutil.copy2(caminho_novo_exe, novo_exe_copia)

    pasta = Path(exe_atual).parent
    bat = str(pasta / "_update_replace.bat")
    with open(bat, "w", encoding="ascii") as f:
        f.write("@echo off\n")
        f.write("timeout /t 2 /nobreak >nul\n")
        f.write(f'move /y "{novo_exe_copia}" "{exe_atual}"\n')
        f.write(f'start "" "{exe_atual}"\n')
        f.write('del "%~f0"\n')

    subprocess.Popen(["cmd", "/c", bat], shell=False,
                     creationflags=subprocess.CREATE_NO_WINDOW)


def reiniciar():
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)
