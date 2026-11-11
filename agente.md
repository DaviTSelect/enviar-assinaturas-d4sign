# Contexto do Projeto para Agente IA

## O que este projeto faz

Bot de automação que lê uma planilha Excel (`Pasta1.xlsx`) e envia documentos para assinatura via D4Sign através de automação web (Selenium/Playwright).

## Tecnologias

- Python 3.10+
- Selenium / automação web de browser
- openpyxl (leitura de Excel)

## Arquitetura

```
enviar-assinaturas-d4sign/
├── main.py         # ponto de entrada; chama Interface()
├── interface.py    # lógica de UI e fluxo principal
├── navegador.py    # automação web: login, envio de documentos D4Sign
├── Pasta1.xlsx     # planilha de entrada (NÃO versionar com dados reais)
├── requeriments.txt  # dependências (nome com typo legado)
├── .env            # credenciais (NÃO versionar)
└── logs/           # logs de execução (NÃO versionar)
```

## Como executar

```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

## Padrões do projeto

- Credenciais via .env (nunca hardcodadas)
- Logs em `logs/`

## O que NÃO fazer

- Não commitar `.env` com credenciais
- Não commitar `Pasta1.xlsx` com dados reais
- Não renomear `requeriments.txt` (typo legado — mantido para compatibilidade)
