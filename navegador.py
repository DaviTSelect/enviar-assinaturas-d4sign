import os
import time
from pathlib import Path

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
load_dotenv()

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")
ID_CHECKBOX_ASSINATURAS = "checkboxFluxo"

# Usuário atual do Windows
user_profile = Path(os.environ["USERPROFILE"])

# Caminhos relativos ao usuário atual
chrome_driver = user_profile / os.getenv("CHROME_DRIVER")
chrome_binary = user_profile / os.getenv("CHROME_BINARY")
log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configuração do Chrome
options = Options()
options.binary_location = str(chrome_binary)

service = Service(
    str(chrome_driver),
    log_output=str(log_dir / "chromedriver.log"),
    service_args=["--verbose"],
)


class Navegador:
    def __init__(self, callback_cofres=None):
        self.driver = webdriver.Chrome(
            service=service,
            options=options
        )
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


    def upload_documento(self,caminho_arquivo):
        input_arquivo = self.wait.until(
        EC.presence_of_element_located(
            (By.ID, "fileupload")
            )
        )

        # Envia o arquivo diretamente para o input
        input_arquivo.send_keys(caminho_arquivo)

        print(f"Arquivo selecionado: {caminho_arquivo}")
        # Algumas telas do D4Sign exigem iniciar o analisador após o upload.
        try:
            botao_analyzer = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "botao-analyzer"))
            )
        except TimeoutException:
            botao_analyzer = None

        if botao_analyzer and botao_analyzer.text.strip() == "Começar":
            botao_analyzer.click()
            print("Analisador iniciado pelo botão Começar.")

        # O D4Sign direciona para a tela do documento após concluir o upload.
        self.wait.until(EC.url_contains("/desk/viewblob/"))
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        self.driver.refresh()
        self.wait.until(EC.url_contains("/desk/viewblob/"))
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        self.wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".ibox-content.menuviewblob #form-carregar-assinaturas")
            )
        )
        print("Upload concluído; tela do documento carregada.")

        if not self.instrucoes_confirmadas:
            try:
                botao_instrucoes = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'a.btn.btn-primary[href="javascript: fechar_instrucoes();"]')
                    )
                )
            except TimeoutException:
                # O aviso pode não aparecer depois da primeira utilização.
                self.instrucoes_confirmadas = True
            else:
                botao_instrucoes.click()
                self.instrucoes_confirmadas = True

        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//span[contains(@class, 'label-warning') and normalize-space()='AGUARDANDO SIGNATÁRIOS']")
            )
        )

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
        campo_email = self.wait.until(
            EC.element_to_be_clickable((By.ID, "email-assinatura"))
        )
        campo_email.clear()
        campo_email.send_keys(email)

        botao_adicionar = self.wait.until(
            EC.element_to_be_clickable((By.ID, "adicionar-assinatura"))
        )
        botao_adicionar.click()

        self.wait.until(
            EC.text_to_be_present_in_element((By.ID, "lista-assinatura"), email)
        )
        print(f"Signatário adicionado: {email}")

    def adicionar_emails(self, emails):
        emails = list(dict.fromkeys(email.strip() for email in emails if email and email.strip()))
        if not emails:
            raise ValueError("Adicione ao menos um e-mail de signatário.")
        print(f"Adicionando {len(emails)} signatário(s)...")
        for indice, email in enumerate(emails, start=1):
            print(f"[{indice}/{len(emails)}] Adicionando {email}...")
            self.adicionar_email(email)

        checkbox = self.wait.until(
            EC.element_to_be_clickable((By.ID, ID_CHECKBOX_ASSINATURAS))
        )
        checkbox.click()
        print("Todos os e-mails foram adicionados; checkbox marcado.")
        time.sleep(5)
        print("Espera de 5 segundos concluída; aguardando carregamento completo da página...")
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        print("Página carregada completamente.")
    def envio_para_assinatura(self, texto):
        if not texto or not texto.strip():
            raise ValueError("O texto da mensagem para assinatura não pode ficar vazio.")

        print("Aguardando o botão 'Enviar para assinatura'...")
        botao_enviar = self.wait.until(
            EC.element_to_be_clickable((By.ID, "enviar-para-assinatura"))
        )
        botao_enviar.click()
        print("Botão 'Enviar para assinatura' clicado; aguardando o editor da mensagem...")

        editor = self.wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".note-editable.card-block[contenteditable='true'][role='textbox']")
            )
        )
        editor.click()
        editor.send_keys(Keys.CONTROL, "a")
        editor.send_keys(texto)
        texto_inserido = self.driver.execute_script("return arguments[0].innerText;", editor) or editor.text
        if " ".join(texto.strip().split()) not in " ".join(texto_inserido.strip().split()):
            raise RuntimeError("Não foi possível confirmar o texto no editor da mensagem.")
        print("Mensagem inserida e conferida no editor.")

        print("Aguardando o botão para salvar e enviar...")
        botao_salvar = self.wait.until(
            EC.element_to_be_clickable((By.ID, "btnSalvarDocumento"))
        )
        botao_salvar.click()
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





