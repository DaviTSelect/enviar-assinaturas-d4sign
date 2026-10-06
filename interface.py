from navegador import Navegador

class Interface():
    def __init__(self):
        self.root = None
        self.cor_primaria = "#00000"
        self.cor_secundaria = '#00000'
        self.logo = 'icon/logo.ico'
        self.planilha = None
        self.documentos = []
        self.status_linha = None
        self.navegador = Navegador()
    def selecionar_planilha(self):
        pass
    def selecionar_documentos(self):
        pass
    def montar_interface(self):
        pass
    def att_interface_status(self):
        pass
    def processar_envio(self):
        self.navegador.abrir_tela_envio()
        self.navegador.garantir_tela_envio()
        self.navegador.adicionar_email()
        self.navegador.confirmar_envio()
        
    def iniciar_automacao(self):
        
        if self.navegador.status_login == None:
            self.navegador.realizar_login()
        for row in self.planilha.iterrows():
            self.processar_envio()
            self.att_interface_status()
        # mensagem para confirmar envio!