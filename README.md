# Enviar Assinaturas D4Sign

Bot de automação que lê uma planilha Excel e envia documentos para assinatura via D4Sign (automação web com Selenium/Playwright).

## Tecnologias

- Python 3.10+
- Selenium / automação web
- openpyxl (leitura de Excel)

## Pré-requisitos

- Python 3.10+
- Google Chrome instalado
- ChromeDriver compatível com a versão do Chrome

## Instalação

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requeriments.txt
```

> **Nota:** o arquivo de dependências é `requeriments.txt` (typo legado — não renomear para manter compatibilidade).

## Configuração

```powershell
# Preencher variáveis de ambiente
cp .env.example .env
# Editar .env com credenciais D4Sign
```

## Uso

```powershell
# Preencher Pasta1.xlsx com os dados de envio
python main.py
```

A execução lê `Pasta1.xlsx`, navega no D4Sign e envia os documentos.
Logs de execução são salvos em `logs/`.

## Estrutura

```
enviar-assinaturas-d4sign/
├── main.py         # ponto de entrada
├── interface.py    # interface de usuário
├── navegador.py    # automação web (Selenium/Playwright)
├── Pasta1.xlsx     # planilha de entrada (não versionar com dados reais)
├── requeriments.txt
├── .env            # credenciais (não versionar)
├── .env.example    # modelo de variáveis
├── relatorio.md    # notas de execução
└── logs/           # logs de execução (não versionados)
```

## Padrão Corporativo

Este projeto segue o [Padrão de Engenharia da Empresa](../PADRAO_EMPRESA/specs/00_PADRAO_GERAL.spec.md).
Categoria: **AUTO** (automação/bot).
