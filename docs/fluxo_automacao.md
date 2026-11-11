# Fluxo de Automação D4Sign

## Visão geral

```
[Interface] Selecionar pasta + planilha
     ↓
[Interface] Confirmar seleção → valida planilha e lista PDFs
     ↓
[Interface] Iniciar automação → abre Chrome, faz login via .env
     ↓
[D4Sign] Abre modal de envio → carrega lista de cofres
     ↓
[Interface] Usuário escolhe cofre + digita mensagem → clica Continuar
     ↓
Para cada documento na planilha:
  [D4Sign] Seleciona cofre → faz upload do PDF
  [D4Sign] Aguarda página viewblob carregar
  [D4Sign] Adiciona cada e-mail como signatário
  [D4Sign] Marca checkbox de fluxo
  [D4Sign] Clica "Enviar para assinatura" → digita mensagem → salva
  Se houver próximo documento: volta à tela de envio
```

---

## Etapa 1 — Login

- **Credenciais:** lidas do arquivo `.env` (variáveis `USUARIO` e `SENHA`). Nunca exibidas na interface.
- **URL de login:** `https://secure.d4sign.com.br/login.html`
- **Confirmação:** presença do elemento `#drop-zone` na URL `https://secure.d4sign.com.br/desk.html`

---

## Etapa 2 — Abertura do modal de envio

- Clica no link `a[href="javascript: eModalDocumento();"]`
- Modal exibe: select de cofres (`name="uuid-cofre"`)
- A automação lê todas as opções (exceto `value="0"`) e as envia para a interface

---

## Etapa 3 — Seleção de cofre (feita pelo usuário na interface)

- O cofre escolhido é **fixo para todos os documentos** do lote
- O usuário também digita a **mensagem** que será enviada a cada signatário

---

## Etapa 4 — Upload do documento

1. Seleciona o cofre no select (mesmo valor para todos)
2. Envia o caminho do PDF para `input#fileupload`
3. Aguarda redirecionamento para `/desk/viewblob/<uuid>.html`
4. **Se aparecer** o botão `#botao-analyzer` com texto "Começar" → clica (ocorre na 1ª vez ou após atualização)
5. **Se aparecer** o modal "Ok, entendi!" → clica no link `fechar_instrucoes()` (ocorre apenas nas primeiras utilizações)
6. Aguarda o campo `#email-assinatura` ficar visível
7. Aguarda o label `AGUARDANDO SIGNATÁRIOS` aparecer

---

## Etapa 5 — Adição de signatários

Para cada e-mail da linha da planilha (na ordem: favorecido → coordenador → diretoria):
1. Limpa e preenche `#email-assinatura`
2. Clica `#adicionar-assinatura`
3. Aguarda o e-mail aparecer em `#lista-assinatura`

Após todos os e-mails:
- Clica no checkbox `#checkboxFluxo`
- Aguarda 5 s + `document.readyState === 'complete'`

---

## Etapa 6 — Envio para assinatura

1. Clica em `#enviar-para-assinatura`
2. Aguarda o editor de mensagem (`.note-editable[contenteditable='true']`)
3. Seleciona todo o texto existente (Ctrl+A) e digita a mensagem configurada na interface
4. Verifica que o texto foi inserido corretamente
5. Clica em `#btnSalvarDocumento`

---

## Etapa 7 — Próximo documento

Se ainda houver documentos na fila:
- Navega de volta para `https://secure.d4sign.com.br/desk.html`
- Reabre o modal de envio
- Reseleciona o mesmo cofre
- Repete a partir da Etapa 4

---

## Erros comuns

| Situação | Causa provável | Onde verificar |
|---|---|---|
| Login falha | Credenciais incorretas no `.env` | `.env` → `USUARIO`, `SENHA` |
| Nenhum cofre encontrado | Conta sem cofres configurados | D4Sign → painel de cofres |
| Arquivo não encontrado | Nome na planilha não bate com o PDF | `docs/planilha.md` → regras de correspondência |
| Timeout no upload | PDF muito grande (>20 MB) ou conexão lenta | Tamanho do arquivo |
| E-mail não adicionado | E-mail inválido ou já existente no documento | Coluna na planilha |
| `btnSalvarDocumento` não encontrado | Mensagem não digitada ou editor não carregou | Campo de mensagem na interface |

---

## Configuração do ambiente

Arquivo `.env` na raiz do projeto:

```
USUARIO=seu_email@dominio.com
SENHA=sua_senha
CHROME_DRIVER=caminho\relativo\ao\userprofile\chromedriver.exe
CHROME_BINARY=caminho\relativo\ao\userprofile\chrome.exe
```
