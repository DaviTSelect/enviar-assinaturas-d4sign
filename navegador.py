import os
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
load_dotenv()

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")

# Usuário atual do Windows
user_profile = Path(os.environ["USERPROFILE"])

# Caminhos relativos ao usuário atual
chrome_driver = user_profile / os.getenv("CHROME_DRIVER")
chrome_binary = user_profile / os.getenv("CHROME_BINARY")

# Configuração do Chrome
options = Options()
options.binary_location = str(chrome_binary)

service = Service(str(chrome_driver))


class Navegador:
    def __init__(self):
        self.driver = webdriver.Chrome(
            service=service,
            options=options
        )
        self.url = 'https://secure.d4sign.com.br/desk.html'
        self.status_login = False
        self.documento = None
        self.lista_email = []
        self.wait = WebDriverWait(self.driver, 10)
        self.cofre = None

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
        print("Login realizado com sucesso!")

    def abrir_tela_envio(self):
        pass
    def garantir_tela_envio(self):
        pass
    def confirmar_envio(self):
        pass
    def adicionar_email(self):
        pass
    def realizar_envio_completo(self):
        pass


        
                
                
