"""
Diário do envio em andamento.

Cada passo é gravado em disco (com fsync) antes e depois de cada documento. Se o
programa for morto ou o computador desligar, o que já foi enviado é recuperado na
próxima abertura. O arquivo é apagado quando a planilha é salva.
"""
import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path

_TIPOS = {"datetime": dt.datetime, "date": dt.date, "time": dt.time}


def _codificar(valor):
    if type(valor).__name__ in _TIPOS:
        return {"$tipo": type(valor).__name__, "v": valor.isoformat()}
    return str(valor)


def _decodificar(objeto):
    if "$tipo" in objeto:
        return _TIPOS[objeto["$tipo"]].fromisoformat(objeto["v"])
    return objeto


def assinatura(caminho) -> str:
    """Identifica o conteúdo da planilha, para não sobrescrever edições posteriores."""
    try:
        return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()
    except OSError:
        return ""


class Diario:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def iniciar(self, planilha: str, documentos: list, duplicadas: list) -> None:
        if self.caminho.exists():
            self.arquivar()  # nunca descartar um registro ainda não recuperado
        self._anexar({
            "planilha": str(planilha),
            "assinatura": assinatura(planilha),
            "documentos": [{"linhas_planilha": d.get("linhas_planilha", [])} for d in documentos],
            "duplicadas": [{"valores": l["valores"]} for l in duplicadas],
        })

    def marcar(self, indice: int, estado: str, mensagem: str = "") -> None:
        """estado: "enviando", "enviado" ou "erro"."""
        self._anexar({"i": indice, "estado": estado, "mensagem": mensagem})

    def _anexar(self, registro: dict) -> None:
        with open(self.caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=_codificar) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def ler(self):
        """(cabeçalho, {índice: último registro}) ou None se não há envio pendente."""
        if not self.caminho.exists():
            return None
        registros = []
        for linha in self.caminho.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                registros.append(json.loads(linha, object_hook=_decodificar))
            except ValueError:
                break  # linha cortada por queda de energia
        if not registros or "documentos" not in registros[0]:
            return None
        return registros[0], {r["i"]: r for r in registros[1:]}

    def concluir(self) -> None:
        self.caminho.unlink(missing_ok=True)

    def arquivar(self) -> Path:
        destino = self.caminho.with_name(f"{self.caminho.stem}_{time.strftime('%Y%m%d_%H%M%S')}.jsonl")
        os.replace(self.caminho, destino)
        return destino
