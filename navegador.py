from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
from dotenv import load_dotenv
load_dotenv()

global USUARIO
USUARIO = os.getenv("USUARIO")

global SENHA
SENHA = os.getenv("SENHA")
# realizar login

def realizar_login():
    
    print(USUARIO)
    options = Options()
    options.binary_location = r"C:\Users\DaviFontouraGaldino\Chrome\GoogleChrome\App\Chrome-bin\chrome.exe"

    service = Service(
        r"C:\Users\DaviFontouraGaldino\Chrome\chromedriver.exe"
    )

    driver = webdriver.Chrome(
        options=options,
        service=service
    )

    driver.get("https://secure.d4sign.com.br/login.html")

    

    
    #achar elementos login
    driver.find_element("id", "Email").send_keys(USUARIO)
    driver.find_element("id", "Passwd").send_keys(SENHA)
    driver.find_element("id", "logar").click()

    S
    return driver
def enviar_assinatura(driver):
    input("Digite ENTER para fechar...")
    