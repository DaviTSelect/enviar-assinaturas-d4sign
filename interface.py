from pathlib import Path
import logging
import re
import threading
import unicodedata

import customtkinter as ctk
from tkinter import filedialog, messagebox
from openpyxl import load_workbook

from navegador import Navegador


LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
ERROR_LOG = LOG_DIR / "automation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(threadName)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(ERROR_LOG, encoding="utf-8")],
)
logger = logging.getLogger(__name__)


class Interface:
    def __init__(self):
        self.planilha = None
        self.pasta_documentos = None
        self.documentos = []
        self.lista_cofres = []
        self.navegador = None
        self.automacao_em_andamento = False
        self.montar_interface()
        # O navegador é criado somente ao iniciar, evitando abrir o Chrome ao
        # abrir a janela durante os testes da interface.
        self.janela.mainloop()

    def montar_interface(self):
        ctk.set_appearance_mode("system")
        self.janela = ctk.CTk()
        self.janela.title("Enviar Assinaturas")
        self.janela.geometry("680x650")
        self.janela.minsize(600, 480)

        self.layout = ctk.CTkFrame(self.janela, fg_color="transparent")
        self.layout.pack(fill="both", expand=True, padx=28, pady=24)
        self.layout.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.layout, text="Envio de assinaturas", font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        ctk.CTkLabel(
            self.layout,
            text="Selecione os arquivos e confirme antes de iniciar a automação.",
            text_color=("gray35", "gray70"),
        ).grid(row=1, column=0, sticky="w", pady=(0, 20))

        self.pasta_label = self._linha_arquivo(2, "Pasta de documentos", self.selecionar_documentos)
        self.planilha_label = self._linha_arquivo(3, "Planilha", self.selecionar_planilha)

        self.confirmar_button = ctk.CTkButton(
            self.layout, text="Confirmar seleção", command=self.confirmar_selecao, state="disabled"
        )
        self.confirmar_button.grid(row=4, column=0, sticky="ew", pady=(14, 8))
        self.iniciar_button = ctk.CTkButton(
            self.layout, text="Iniciar automação", command=self.iniciar_automacao, state="disabled"
        )
        self.iniciar_button.grid(row=5, column=0, sticky="ew", pady=8)

        self.status_label = ctk.CTkLabel(
            self.layout, text="Modo de teste: os documentos de exemplo do código serão usados.",
            anchor="w", justify="left", wraplength=600,
        )
        self.status_label.grid(row=6, column=0, sticky="ew", pady=(12, 10))

        ctk.CTkLabel(
            self.layout, text="Texto da mensagem para assinatura", anchor="w"
        ).grid(row=7, column=0, sticky="ew", pady=(4, 2))
        self.mensagem_texto = ctk.CTkTextbox(self.layout, height=90, wrap="word")
        self.mensagem_texto.grid(row=8, column=0, sticky="ew", pady=(0, 8))
        self.mensagem_texto.insert("1.0", "")

        self.cofre_frame = ctk.CTkFrame(self.layout)
        self.cofre_frame.grid(row=9, column=0, sticky="ew", pady=(8, 0))
        self.cofre_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.cofre_frame, text="Cofres disponíveis", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 4)
        )
        self.cofre_var = ctk.StringVar(value="")
        self.cofre_menu = ctk.CTkOptionMenu(self.cofre_frame, variable=self.cofre_var, values=["Aguardando automação"])
        self.cofre_menu.grid(row=1, column=0, sticky="ew", padx=14, pady=(4, 12))
        self.continuar_button = ctk.CTkButton(self.cofre_frame, text="Continuar automação", command=self.continuar_automacao, state="disabled")
        self.continuar_button.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        self.cofre_frame.grid_remove()

    def _linha_arquivo(self, row, titulo, comando):
        frame = ctk.CTkFrame(self.layout)
        frame.grid(row=row, column=0, sticky="ew", pady=7)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 0)
        )
        nome = ctk.CTkLabel(frame, text="Nenhum selecionado", anchor="w", text_color=("gray40", "gray65"))
        nome.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 10))
        ctk.CTkButton(frame, text="Inserir", width=110, command=comando).grid(
            row=0, column=1, rowspan=2, padx=14, pady=10
        )
        return nome

    def selecionar_planilha(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar planilha", filetypes=[("Planilhas Excel", "*.xlsx"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.planilha = caminho
            self.planilha_label.configure(text=Path(caminho).name)
            self._atualizar_confirmacao()

    def selecionar_documentos(self):
        caminho = filedialog.askdirectory(title="Selecionar pasta de documentos")
        if caminho:
            self.pasta_documentos = caminho
            self.pasta_label.configure(text=caminho)
            self._atualizar_confirmacao()

    def _atualizar_confirmacao(self):
        disponivel = bool(self.planilha and self.pasta_documentos)
        self.confirmar_button.configure(state="normal" if disponivel else "disabled")
        self.iniciar_button.configure(state="disabled")

    def confirmar_selecao(self):
        if not self.pasta_documentos or not self.planilha:
            messagebox.showwarning("Seleção incompleta", "Selecione a pasta e a planilha para confirmar.")
            return
        try:
            self.documentos = self.carregar_documentos(self.planilha, self.pasta_documentos)
        except Exception as erro:
            messagebox.showerror("Planilha inválida", str(erro))
            return
        messagebox.showinfo("Seleção confirmada", f"{len(self.documentos)} documento(s) pronto(s) para envio.")
        self.status_label.configure(text=f"Seleção confirmada: {len(self.documentos)} documento(s) e signatários carregados.")
        self.iniciar_button.configure(state="normal")

    @staticmethod
    def _normalizar_cabecalho(valor):
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        return "".join(caractere for caractere in texto if not unicodedata.combining(caractere)).strip().lower().replace(" ", "_")

    @staticmethod
    def _normalizar_nome_arquivo(valor):
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere)).casefold()
        return " ".join(re.findall(r"[a-z0-9]+", texto))

    def carregar_documentos(self, caminho_planilha, pasta_documentos):
        print("Lendo a planilha de signatários...")
        workbook = load_workbook(caminho_planilha, read_only=True, data_only=True)
        planilha = workbook.active
        linhas = planilha.iter_rows(values_only=True)
        cabecalhos = next(linhas, None)
        if not cabecalhos:
            raise ValueError("A planilha está vazia.")
        indices = {self._normalizar_cabecalho(valor): indice for indice, valor in enumerate(cabecalhos) if valor is not None}
        indices_email = [
            indice for cabecalho, indice in indices.items()
            if cabecalho == "email" or cabecalho == "e_mail" or re.fullmatch(r"email_?\d+", cabecalho)
        ]
        indice_arquivo = indices.get("nome_arquivo", indices.get("arquivo", indices.get("documento")))
        indice_nome = indices.get("nome")
        if not indices_email or (indice_arquivo is None and indice_nome is None):
            raise ValueError("A planilha deve ter uma coluna 'nome' (ou 'nome_arquivo') e ao menos uma coluna 'email', 'email1', 'email2' etc.")

        arquivos = [
            arquivo for arquivo in Path(pasta_documentos).iterdir()
            if arquivo.is_file() and arquivo.suffix.casefold() == ".pdf"
        ]
        agrupados = {}
        for numero_linha, valores in enumerate(linhas, start=2):
            if not valores or not any(valor is not None and str(valor).strip() for valor in valores):
                continue
            nome_arquivo = str(valores[indice_arquivo] or "").strip() if indice_arquivo is not None else ""
            nome = str(valores[indice_nome] or "").strip() if indice_nome is not None else ""
            emails = [str(valores[indice] or "").strip() for indice in indices_email if indice < len(valores) and valores[indice] is not None and str(valores[indice]).strip()]
            identificador = Path(nome_arquivo).stem if nome_arquivo else nome
            if not emails or not identificador:
                raise ValueError(f"Linha {numero_linha}: informe nome do documento e ao menos um e-mail.")

            alvo = self._normalizar_nome_arquivo(identificador)
            candidatos = [arquivo for arquivo in arquivos if self._normalizar_nome_arquivo(arquivo.stem) == alvo]
            if not candidatos:
                tokens_nome = alvo.split()
                candidatos = [
                    arquivo for arquivo in arquivos
                    if all(token in self._normalizar_nome_arquivo(arquivo.stem).split() for token in tokens_nome)
                ]
            if not candidatos:
                raise ValueError(f"Linha {numero_linha}: não encontrei arquivo compatível com '{identificador}' na pasta selecionada.")
            if len(candidatos) > 1:
                nomes_candidatos = ", ".join(arquivo.name for arquivo in candidatos)
                raise ValueError(f"Linha {numero_linha}: mais de um arquivo corresponde a '{identificador}': {nomes_candidatos}. Deixe apenas o arquivo correto na pasta ou informe o nome exato na coluna 'nome_arquivo'.")
            arquivo = candidatos[0]
            chave = str(arquivo.resolve())
            if chave not in agrupados:
                agrupados[chave] = {"nome": nome or arquivo.stem, "emails": [], "nome_arquivo": chave}
            agrupados[chave]["emails"].extend(emails)

        workbook.close()
        if not agrupados:
            raise ValueError("A planilha não contém linhas de signatários para processar.")
        documentos = list(agrupados.values())
        print(f"Planilha carregada: {len(documentos)} documento(s), {sum(len(doc['emails']) for doc in documentos)} associação(ões) de e-mail.")
        return documentos

    def iniciar_automacao(self):
        if self.automacao_em_andamento:
            return
        self.automacao_em_andamento = True
        self.iniciar_button.configure(state="disabled")
        self.status_label.configure(text="Iniciando navegador e carregando os cofres...")
        threading.Thread(target=self._executar_teste, daemon=True).start()

    def _executar_teste(self):
        try:
            documentos = self.documentos
            self.navegador = Navegador(self.mostrar_cofres)
            if not self.navegador.status_login:
                self.navegador.realizar_login()
            # Abre o envio para carregar as opções de cofre no painel.
            self.navegador.abrir_tela_envio()
            cofres = self.navegador.carregar_cofres()
            self.janela.after(0, lambda: self.status_label.configure(
                text=f"Navegador pronto: {len(documentos)} documento(s) carregado(s). Selecione o cofre para enviar."
            ))
        except Exception as erro:
            logger.exception("Falha durante a inicialização e leitura dos cofres")
            self.janela.after(0, lambda: self.status_label.configure(
                text=f"Falha na automação. Consulte o log: {ERROR_LOG}"
            ))
        finally:
            self.automacao_em_andamento = False
            self.janela.after(0, lambda: self.iniciar_button.configure(state="normal"))

    def _cofres_carregados(self, cofres):
        self.lista_cofres = cofres
        nomes = [cofre["texto"] for cofre in cofres]
        self.cofre_frame.grid()
        self.cofre_menu.configure(values=nomes)
        self.cofre_var.set(nomes[0] if nomes else "Nenhum cofre encontrado")
        self.continuar_button.configure(state="normal" if nomes else "disabled")

    def continuar_automacao(self):
        if self.automacao_em_andamento or not self.lista_cofres:
            return
        cofre = next((item for item in self.lista_cofres if item["texto"] == self.cofre_var.get()), None)
        if not cofre:
            messagebox.showwarning("Cofre inválido", "Selecione um cofre disponível.")
            return
        if not self.documentos:
            messagebox.showwarning("Sem documentos", "Confirme a planilha e a pasta de documentos antes de continuar.")
            return
        texto = self.mensagem_texto.get("1.0", "end").strip()
        if not texto:
            messagebox.showwarning("Mensagem obrigatória", "Digite o texto da mensagem para assinatura.")
            return
        self.automacao_em_andamento = True
        self.continuar_button.configure(state="disabled")
        threading.Thread(target=self._enviar_arquivos, args=(cofre, self.documentos, texto), daemon=True).start()

    def _enviar_arquivos(self, cofre, arquivos, texto):
        try:
            for indice, documento in enumerate(arquivos):
                arquivo = Path(documento["nome_arquivo"])
                print(f"Iniciando {indice + 1}/{len(arquivos)}: {arquivo.name} para {len(documento['emails'])} signatário(s)...")
                self.navegador.selecionar_cofre(cofre["valor"])
                self.navegador.upload_documento(str(arquivo))
                self.navegador.adicionar_emails(documento["emails"])
                self.navegador.envio_para_assinatura(texto)
                if indice + 1 < len(arquivos):
                    self.navegador.voltar_para_envio()
            self.janela.after(0, lambda: self.status_label.configure(text=f"Documentos enviados para assinatura no cofre {cofre['texto']}."))
        except Exception as erro:
            logger.exception("Falha durante o upload dos documentos")
            self.janela.after(0, lambda: self.status_label.configure(
                text=f"Falha no envio. Consulte o log: {ERROR_LOG}"
            ))
        finally:
            self.automacao_em_andamento = False
            self.janela.after(0, lambda: self.continuar_button.configure(state="normal"))

    def mostrar_cofres(self, cofres):
        """Publica as opções na interface a partir da thread do Selenium."""
        self.janela.after(0, lambda: self._cofres_carregados(cofres))
