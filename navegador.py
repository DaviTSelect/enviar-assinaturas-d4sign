import os
import time
from pathlib import Path

import sys

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
# Carrega .env da pasta do executável (ou do script durante desenvolvimento)
_env_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
load_dotenv(_env_dir / ".env")

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")
ID_CHECKBOX_ASSINATURAS = "checkboxFluxo"

log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(exist_ok=True)


def _criar_service():
    user_profile = Path(os.environ["USERPROFILE"])
    drv = os.getenv("CHROME_DRIVER")
    bin_ = os.getenv("CHROME_BINARY")
    if not drv or not bin_:
        raise EnvironmentError(
            "CHROME_DRIVER e CHROME_BINARY não encontrados no .env.\n"
            f"Verifique se o arquivo .env está em: {_env_dir}"
        )
    return (
        Service(
            str(user_profile / drv),
            log_output=str(log_dir / "chromedriver.log"),
            service_args=["--verbose"],
        ),
        str(user_profile / bin_),
    )


class Navegador:
    def __init__(self, callback_cofres=None, headless=False):
        service, chrome_binary = _criar_service()
        opts = Options()
        opts.binary_location = chrome_binary
        if headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--window-size=1366,768")
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.url = 'https://secure.d4sign.com.br/desk.html'
        self.status_login = False
        self.documento = None
        self.lista_email = []
        self.wait = WebDriverWait(self.driver, 10)
        self.lista_cofres = None
        self.cofre_selecionado = None
        self.upload_arquivo = False
        self.emails_inseridos = False
        self.callback_cofres = callback_cofres
        self.instrucoes_confirmadas = False


    def realizar_login(self):
        self.driver.get(self.url)
        #email
        campo_email = self.wait.until(EC.element_to_be_clickable((By.ID, "Email")))
        campo_email.send_keys(USUARIO)
        #senha
        campo_senha = self.wait.until(EC.element_to_be_clickable((By.ID, "Passwd")))
        campo_senha.send_keys(SENHA)
        #entrar
        campo_entrar = self.wait.until(EC.element_to_be_clickable((By.ID, "logar")))
        campo_entrar.click()
        campo_site = self.wait.until(EC.element_to_be_clickable((By.ID, "drop-zone")))
        self.status_login = True
        print("Login realizado com sucesso!")


    def abrir_tela_envio(self):
        print("clicar no local de subir arquivo")
        elemento = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//p[contains(@class, 'btn-primary') and contains(normalize-space(), 'Clique ou arraste aqui')]"
                    )
                )
            )

        botao_upload = self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a[href="javascript: eModalDocumento();"]')
            )
        )
        botao_upload.click()
        print("Tela de envio aberta; aguardando carregamento das opções de cofre")




    def garantir_tela_envio(self):
        pass
    def carregar_cofres(self):
        elemento = self.wait.until(
            EC.element_to_be_clickable(
                (By.NAME, "uuid-cofre")
            )
        )

        select = Select(elemento)

        lista_cofres = []

        for opcao in select.options:
            texto = opcao.text.strip()
            valor = opcao.get_attribute("value")

            print(f"Texto: {texto} | Value: {valor}")

            # Ignora a opção "Escolha um cofre"
            if valor and valor != "0":
                lista_cofres.append({
                    "texto": texto,
                    "valor": valor
                })

        if not lista_cofres:
            raise Exception("Nenhum cofre disponível para seleção.")

        self.lista_cofres = lista_cofres
        if self.callback_cofres:
            self.callback_cofres(lista_cofres)
        return lista_cofres

    def selecionar_cofre(self, valor):
        elemento = self.wait.until(EC.element_to_be_clickable((By.NAME, "uuid-cofre")))
        Select(elemento).select_by_value(valor)
        self.cofre_selecionado = valor
        return valor


    # ── Utilitários internos ──────────────────────────────────────────────────

    def _aguardar_pagina_livre(self, timeout=15):
        """Aguarda que não haja modal-backdrop nem overlay de loading visíveis."""
        seletores_bloqueio = [
            ".modal-backdrop",
            "#loading",
            ".loading",
            "#overlay",
            ".overlay",
            "[class*='loading'][style*='display: block']",
            "[class*='spinner'][style*='display: block']",
        ]
        for seletor in seletores_bloqueio:
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, seletor))
                )
            except TimeoutException:
                pass

    def _aguardar_sem_backdrop(self, timeout=15):
        """Aguarda até que nenhum modal-backdrop esteja visível na página."""
        self._aguardar_pagina_livre(timeout)

    def _clicar(self, elemento):
        """Tenta clicar normalmente; usa JavaScript como fallback se interceptado."""
        try:
            elemento.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", elemento)

    def _snapshot(self, nome):
        """Salva HTML + URL atuais em logs/snapshots/ para diagnóstico."""
        try:
            snap_dir = Path(__file__).resolve().parent / "logs" / "snapshots"
            snap_dir.mkdir(exist_ok=True)
            ts = time.strftime("%H%M%S")
            arq = snap_dir / f"{ts}_{nome}.html"
            arq.write_text(
                f"<!-- URL: {self.driver.current_url} -->\n{self.driver.page_source}",
                encoding="utf-8"
            )
            print(f"[snapshot] {arq.name}")
        except Exception as e:
            print(f"[snapshot] falha: {e}")

    # ── Upload ────────────────────────────────────────────────────────────────

    def upload_documento(self, caminho_arquivo):
        caminho_arquivo = str(Path(caminho_arquivo).resolve())
        if not Path(caminho_arquivo).is_file():
            raise FileNotFoundError(f"Arquivo para upload não encontrado: {caminho_arquivo}")

        self._snapshot("1_antes_upload")
        input_arquivo = self.wait.until(
            EC.presence_of_element_located((By.ID, "fileupload"))
        )
        input_arquivo.send_keys(caminho_arquivo)
        print(f"Arquivo selecionado: {caminho_arquivo}")
        self._snapshot("2_apos_send_keys")

        # Botão "Começar" do analisador D4Sign (aparece na 1ª vez ou após atualização)
        try:
            botao_analyzer = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "botao-analyzer"))
            )
        except TimeoutException:
            botao_analyzer = None

        if botao_analyzer and botao_analyzer.text.strip() == "Começar":
            self._clicar(botao_analyzer)
            self._aguardar_sem_backdrop()
            self._snapshot("3_apos_analyzer")
            print("Analisador iniciado pelo botão Começar.")

        # Aguarda abertura da tela viewblob em qualquer aba
        janela_atual = self.driver.current_window_handle

        def tela_documento_aberta(driver):
            for janela in driver.window_handles:
                driver.switch_to.window(janela)
                if "/desk/viewblob/" in driver.current_url:
                    return True
                if driver.find_elements(By.ID, "email-assinatura"):
                    return True
            if janela_atual in driver.window_handles:
                driver.switch_to.window(janela_atual)
            return False

        try:
            WebDriverWait(self.driver, 60).until(tela_documento_aberta)
            self._snapshot("4_viewblob_aberto")
        except TimeoutException as erro:
            self._snapshot("4_timeout_viewblob")
            raise TimeoutException(
                "O D4Sign não abriu a tela do documento após selecionar o arquivo "
                f"(URL: {self.driver.current_url}; título: {self.driver.title}). "
                "Verifique se o upload foi aceito e se apareceu alguma mensagem no site."
            ) from erro

        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

        # Modal "Ok, entendi!" com instrucoes de assinatura posicionada (1ª vez)
        if not self.instrucoes_confirmadas:
            try:
                botao_instrucoes = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'a.btn.btn-primary[href="javascript: fechar_instrucoes();"]')
                    )
                )
            except TimeoutException:
                self.instrucoes_confirmadas = True
            else:
                self._snapshot("5_antes_fechar_instrucoes")
                self._clicar(botao_instrucoes)
                self._aguardar_sem_backdrop()
                self._snapshot("5_apos_fechar_instrucoes")
                self.instrucoes_confirmadas = True

        # Garante que não há backdrop restante antes de interagir com signatários
        self._aguardar_sem_backdrop()

        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "email-assinatura")))
            self._snapshot("6_email_assinatura_visivel")
        except TimeoutException as erro:
            self._snapshot("6_timeout_email_assinatura")
            raise TimeoutException(
                "O upload terminou, mas o campo de e-mail não apareceu na tela do documento "
                f"(URL: {self.driver.current_url}; título: {self.driver.title})."
            ) from erro

        # Verifica label de status — usa contains para evitar problemas de encoding com 'Á'
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//span[contains(@class,'label-warning') and contains(.,'AGUARDANDO')]")
                )
            )
            self._snapshot("7_aguardando_signatarios")
        except TimeoutException:
            # Campo email já visível — prossegue mesmo sem confirmar o label
            self._snapshot("7_label_nao_encontrado_mas_ok")
            print("Label AGUARDANDO não encontrado, mas email-assinatura visível — prosseguindo.")

    def voltar_para_envio(self):
        self.driver.get(self.url)
        self.wait.until(EC.element_to_be_clickable((By.ID, "drop-zone")))
        self.abrir_tela_envio()
        self.selecionar_cofre(self.cofre_selecionado)
    def confirmar_envio(self):
        pass
    def adicionar_email(self, email):
        email = email.strip()
        if not email:
            raise ValueError("O e-mail do signatário não pode ficar vazio.")

        self._aguardar_pagina_livre()
        self._snapshot(f"8_antes_adicionar_{email[:20].replace('@','_')}")

        campo_email = self.wait.until(EC.element_to_be_clickable((By.ID, "email-assinatura")))
        campo_email.clear()
        campo_email.send_keys(email)

        botao_adicionar = self.wait.until(EC.element_to_be_clickable((By.ID, "adicionar-assinatura")))
        self._clicar(botao_adicionar)

        self.wait.until(EC.text_to_be_present_in_element((By.ID, "lista-assinatura"), email))
        self._snapshot(f"9_email_adicionado_{email[:20].replace('@','_')}")
        print(f"Signatário adicionado: {email}")

    def adicionar_emails(self, emails):
        emails = list(dict.fromkeys(email.strip() for email in emails if email and email.strip()))
        if not emails:
            raise ValueError("Adicione ao menos um e-mail de signatário.")
        print(f"Adicionando {len(emails)} signatário(s)...")
        for indice, email in enumerate(emails, start=1):
            print(f"[{indice}/{len(emails)}] Adicionando {email}...")
            self.adicionar_email(email)

        # Checkbox de fluxo só aparece quando há mais de um signatário.
        if len(emails) > 1:
            try:
                checkbox = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, ID_CHECKBOX_ASSINATURAS))
                )
                self._clicar(checkbox)
                print("Checkbox de fluxo marcado.")
                time.sleep(3)
                self.wait.until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                print("Checkbox de fluxo não encontrado mesmo com múltiplos e-mails — prosseguindo.")
        print("Todos os e-mails foram adicionados.")
    def envio_para_assinatura(self, texto):
        if not texto or not texto.strip():
            raise ValueError("O texto da mensagem para assinatura não pode ficar vazio.")

        self._aguardar_pagina_livre()
        self._snapshot("10_antes_enviar_assinatura")
        print("Aguardando o botão 'Enviar para assinatura'...")
        botao_enviar = self.wait.until(EC.element_to_be_clickable((By.ID, "enviar-para-assinatura")))
        self._clicar(botao_enviar)
        print("Botão 'Enviar para assinatura' clicado; aguardando o editor da mensagem...")

        self._aguardar_pagina_livre()
        editor = self.wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".note-editable.card-block[contenteditable='true'][role='textbox']")
            )
        )
        self._clicar(editor)
        editor.send_keys(Keys.CONTROL, "a")
        editor.send_keys(texto)
        texto_inserido = self.driver.execute_script("return arguments[0].innerText;", editor) or editor.text
        if " ".join(texto.strip().split()) not in " ".join(texto_inserido.strip().split()):
            raise RuntimeError("Não foi possível confirmar o texto no editor da mensagem.")
        print("Mensagem inserida e conferida no editor.")

        self._aguardar_pagina_livre()
        print("Aguardando o botão para salvar e enviar...")
        botao_salvar = self.wait.until(EC.element_to_be_clickable((By.ID, "btnSalvarDocumento")))
        self._clicar(botao_salvar)
        print("Mensagem salva; envio para assinatura solicitado.")

    def realizar_envio_completo(self, documento, texto):
        nome = documento["nome"]
        emails = documento["emails"]
        nome_arquivo = documento["nome_arquivo"]

        print(f"Enviando documento para {nome} - {len(emails)} signatário(s)")
        print(f"Arquivo: {nome_arquivo}")
        if not self.status_login:
            self.realizar_login()
        self.abrir_tela_envio()
        self.upload_documento(nome_arquivo)
        self.adicionar_emails(emails)
        self.envio_para_assinatura(texto)
        self.confirmar_envio()





