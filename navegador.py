from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# realizar login

def realizar_login():
    options = Options()
    options.binary_location = r"C:\Users\DaviTorresdeSousa\Chrome\GoogleChrome\App\Chrome-bin\chrome.exe"

    service = Service(
        r"C:\Users\DaviTorresdeSousa\Chrome\chromedriver.exe"
    )

    driver = webdriver.Chrome(
        options=options,
        service=service
    )

    driver.get("https://secure.d4sign.com.br/login.html")

    input("Digite ENTER para fechar...")

    return driver