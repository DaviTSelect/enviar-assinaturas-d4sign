from navegador import realizar_login
from navegador import enviar_assinatura
if __name__ == "__main__":
    navegador = realizar_login()
    navegador = enviar_assinatura(navegador)