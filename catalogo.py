"""
Árvore de cofres e subpastas do D4Sign, lida do menu lateral.

Mesma lógica do projeto baixar-d4sign-centralbolsas (discovery.py): os itens
liCofre_*/liFolder_* são lidos do HTML e as subpastas só são carregadas quando o
ramo é expandido.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from selenium.webdriver.support.ui import WebDriverWait

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
_EXPANDIR = r"(?:o_subpastas|accordion_pastas(?:_shared)?)"
_MAIS_PAGINAS = "[onclick*='maissubpastas'], [href*='maissubpastas']"


@dataclass(eq=False)
class Destino:
    """Um cofre (raiz) ou uma subpasta que pode receber documentos."""
    id_cofre: str
    uuid: str
    nome: str
    uuid_cofre: str
    url: str = ""
    dom_id: str = ""
    expansivel: bool = False
    carregado: bool = True
    pai: "Destino | None" = None
    filhos: list = field(default_factory=list)

    @property
    def chave(self) -> str:
        return f"{self.id_cofre}:{self.uuid}"

    @property
    def uuid_pasta(self) -> str:
        """Vazio quando o destino é o próprio cofre."""
        return "" if self.uuid == self.uuid_cofre else self.uuid

    @property
    def caminho(self) -> str:
        return f"{self.pai.caminho} / {self.nome}" if self.pai else self.nome


def partes_do_link(href: str, base: str):
    """(id do cofre, [uuid do cofre, ..., uuid da pasta], url) ou None."""
    url = urlsplit(urljoin(base, href))
    if url.scheme != "https" or url.netloc != urlsplit(base).netloc:
        return None
    partes = url.path.rstrip("/").removesuffix(".html").split("/")
    if len(partes) < 5 or partes[1:3] != ["desk", "cofres"] or not partes[3].isdigit():
        return None
    if not all(_UUID.fullmatch(p) for p in partes[4:]):
        return None
    return partes[3], [p.lower() for p in partes[4:]], url._replace(query="", fragment="").geturl()


class _MenuParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.itens, self.pilha, self.nomes, self.links = [], [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "li":
            identidade = attrs.get("id") or ""
            item = None
            if re.fullmatch(r"li(?:Cofre|Folder)_\d+", identidade):
                item = dict(
                    id=identidade, classes=(attrs.get("class") or "").split(),
                    nome="", href="", expansivel=False,
                    pai=next((r["id"] for r in reversed(self.pilha) if r), ""),
                )
                self.itens.append(item)
            self.pilha.append(item)
        item = next((r for r in reversed(self.pilha) if r), None)
        if not item:
            return
        if tag == "a" and "/desk/cofres/" in (attrs.get("href") or ""):
            item["href"] = attrs["href"]
            self.links.append(item)
        if tag == "span":
            nomeado = {"nome_cofre", "nome_pasta"} & set((attrs.get("class") or "").split())
            self.nomes.append(item if nomeado else None)
        if re.search(rf"\b{_EXPANDIR}\s*\(", attrs.get("onclick") or ""):
            item["expansivel"] = True

    def handle_endtag(self, tag):
        if tag == "li" and self.pilha:
            self.pilha.pop()
        if tag == "span" and self.nomes:
            self.nomes.pop()
        if tag == "a" and self.links:
            self.links.pop()

    def handle_data(self, texto):
        if self.nomes and self.nomes[-1]:
            self.nomes[-1]["nome"] += texto
        elif self.links:
            # Marcação antiga: nome direto dentro do <a>
            texto = texto.strip()
            if texto and not texto.startswith("javascript:"):
                self.links[-1]["nome"] += texto + " "


def itens_do_menu(html: str) -> list[dict]:
    parser = _MenuParser()
    parser.feed(html)
    return parser.itens


class Catalogo:
    def __init__(self, driver, url_desk: str, timeout: int = 30):
        self.driver, self.url_desk, self.timeout = driver, url_desk, timeout
        self.nos: dict[str, Destino] = {}
        self.raizes: list[Destino] = []

    # ── Montagem da árvore ────────────────────────────────────────────────────

    def juntar(self, itens: list[dict], expandido: Destino | None = None) -> None:
        novos = set()
        for item in itens:
            partes = partes_do_link(item["href"], self.url_desk)
            nome = " ".join(item["nome"].split())
            if not partes or not nome:
                raise RuntimeError("Não foi possível identificar um item do menu do D4Sign.")
            id_cofre, cadeia, url = partes
            chave = f"{id_cofre}:{cadeia[-1]}"
            if chave not in self.nos:
                self.nos[chave] = Destino(
                    id_cofre, cadeia[-1], nome, cadeia[0], url=url, dom_id=item["id"],
                    expansivel=item["expansivel"], carregado=not item["expansivel"],
                )
                novos.add(chave)
            item["chave"], item["cadeia"] = chave, cadeia
        por_dom = {no.dom_id: no for no in self.nos.values()}
        for item in itens:
            no = self.nos[item["chave"]]
            if item["id"].startswith("liCofre_"):
                if no not in self.raizes:
                    self.raizes.append(no)
                continue
            pai = por_dom.get(item["pai"])
            pistas = [c for c in item["classes"] if c.startswith("liFolder_") and c != item["id"]]
            if not pai and pistas:
                pai = por_dom.get(pistas[-1])
            if not pai and len(item["cadeia"]) > 2:
                pai = self.nos.get(f"{no.id_cofre}:{item['cadeia'][-2]}")
            # <li> irmãos recém-inseridos pertencem ao ramo que acabou de abrir
            if not pai and expandido and no.chave in novos:
                pai = expandido
            if not pai:
                pai = self.nos.get(f"{no.id_cofre}:{item['cadeia'][0]}")
            if not pai or pai is no or pai.id_cofre != no.id_cofre:
                raise RuntimeError("Não foi possível determinar a pasta de origem de " + no.nome)
            if no.pai:
                continue
            ancestral = pai
            while ancestral:
                if ancestral is no:
                    raise RuntimeError("O menu retornou uma hierarquia circular.")
                ancestral = ancestral.pai
            no.pai = pai
            pai.filhos.append(no)
        for raiz in self.raizes:
            if raiz.filhos:
                raiz.carregado = True

    # ── Navegação ─────────────────────────────────────────────────────────────

    def _pronto(self) -> None:
        WebDriverWait(self.driver, self.timeout).until(lambda d: d.execute_script(
            "return document.readyState === 'complete' && (!window.jQuery || jQuery.active === 0)"
        ))
        if "/desk" not in self.driver.current_url:
            raise RuntimeError("A sessão expirou. Inicie a automação novamente.")

    def _abrir_painel(self) -> None:
        self.driver.get(self.url_desk)
        self._pronto()

    def carregar(self) -> list[Destino]:
        self._abrir_painel()
        self.nos, self.raizes = {}, []
        self.juntar(itens_do_menu(self.driver.page_source))
        if not self.raizes:
            raise RuntimeError("Nenhum cofre disponível para seleção.")
        return self.raizes

    def expandir(self, no: Destino) -> Destino:
        if no.carregado:
            return no
        if "/desk.html" not in self.driver.current_url:
            self._abrir_painel()
        self._pronto()
        self._revelar(no)
        self._clicar_menu(no)
        self.juntar(itens_do_menu(self.driver.page_source), expandido=no)
        no.carregado = True
        return no

    def _revelar(self, no: Destino) -> None:
        """Ao recarregar o painel, os ramos voltam recolhidos."""
        if self.driver.execute_script("return !!document.getElementById(arguments[0])", no.dom_id):
            return
        if not no.pai:
            raise RuntimeError("O menu mudou. Inicie a automação novamente.")
        self._revelar(no.pai)
        self._clicar_menu(no.pai)

    def _clicar_menu(self, no: Destino) -> None:
        clicou = self.driver.execute_script("""
            const item = document.getElementById(arguments[0]);
            if (!item) return false;
            const controle = Array.from(item.querySelectorAll('[onclick]')).find(
                el => new RegExp(arguments[1] + '\\\\s*\\\\(').test(el.getAttribute('onclick')));
            if (!controle) return false;
            controle.click();
            return true;
        """, no.dom_id, _EXPANDIR)
        if not clicou:
            raise RuntimeError("Não foi possível expandir " + no.nome)
        self._aguardar_menu()
        # Cofres com muitas pastas paginam o menu
        for _ in range(50):
            mais = self.driver.execute_script("""
                const item = document.getElementById(arguments[0]);
                const link = item && item.querySelector(arguments[1]);
                if (!link) return false;
                link.click();
                return true;
            """, no.dom_id, _MAIS_PAGINAS)
            if not mais:
                break
            self._aguardar_menu()

    def _aguardar_menu(self) -> None:
        self._pronto()
        anterior, estavel = None, 0

        def parou(driver):
            nonlocal anterior, estavel
            if not driver.execute_script("return !window.jQuery || jQuery.active === 0"):
                estavel = 0
                return False
            html = driver.page_source
            estavel = estavel + 1 if html == anterior else 0
            anterior = html
            return estavel >= 2

        WebDriverWait(self.driver, self.timeout, poll_frequency=0.3).until(parou)
