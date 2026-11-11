# Release v1.0.0 — Enviar Assinaturas D4Sign

## GitHub Release Info

| Campo      | Valor                                           |
|------------|-------------------------------------------------|
| **Tag**    | `v1.0.0`                                        |
| **Target** | `main`                                          |
| **Título** | Enviar Assinaturas D4Sign v1.0.0                |
| **Tipo**   | Latest release                                  |
| **Anexo**  | `EnviarAssinaturas.exe`                         |

---

## Release Notes

### Primeira versão — Enviar Assinaturas D4Sign

Automação desktop para envio de documentos PDF para assinatura digital via portal D4Sign.

---

### Funcionalidades

- Seleção de pasta de documentos PDF e planilha Excel de signatários
- Correspondência automática de PDF pelo nome (busca exata e por tokens)
- Suporte a múltiplos signatários por documento (email_favorecido, email_coordenador, email_diretoria)
- Seleção de cofre D4Sign por sessão
- Mensagem customizável enviada a cada signatário
- Modo oculto: Chrome em segundo plano (sem janela visível)
- Atualização automática via GitHub Releases
- Relatório ao final: linhas enviadas movidas para aba "Enviados"; erros permanecem na aba original com mensagem

---

### Requisitos

- Windows 10/11
- Chrome portátil + ChromeDriver configurados no `.env`
- Arquivo `.env` na mesma pasta do executável

---

### Instalação

1. Baixe `EnviarAssinaturas.exe`
2. Coloque na pasta desejada junto com o arquivo `.env`
3. Execute `EnviarAssinaturas.exe`

---

### Stack técnica

| Componente  | Biblioteca         |
|-------------|--------------------|
| Interface   | PySide6            |
| Automação   | Selenium WebDriver |
| Planilhas   | openpyxl           |
| Auto-update | GitHub Releases API |
| Compilação  | PyInstaller        |
