# Seletores HTML — D4Sign

Todos os IDs, classes e XPaths usados pelo `navegador.py`.
Se o site mudar algum elemento, edite aqui e ajuste o Python correspondente.

---

## Página de login
**URL:** `https://secure.d4sign.com.br/login.html`

| Elemento | Seletor | Usado em |
|---|---|---|
| Campo e-mail | `By.ID, "Email"` | `realizar_login` |
| Campo senha | `By.ID, "Passwd"` | `realizar_login` |
| Botão entrar | `By.ID, "logar"` | `realizar_login` |
| Confirmação pós-login (drop-zone) | `By.ID, "drop-zone"` | `realizar_login` |

**URL após login:** `https://secure.d4sign.com.br/desk.html`

---

## Abertura do modal de envio
**Gatilho:** clique no link que chama `eModalDocumento()`

| Elemento | Seletor | Usado em |
|---|---|---|
| Link "Clique ou arraste aqui" | `By.CSS_SELECTOR, 'a[href="javascript: eModalDocumento();"]'` | `abrir_tela_envio` |
| Botão "Enviar novo documento" (texto) | `By.XPATH, "//p[contains(@class,'btn-primary') and contains(normalize-space(),'Clique ou arraste aqui')]"` | `abrir_tela_envio` (verificação) |

---

## Modal de upload — seleção do cofre
**Aparece após `abrir_tela_envio()`**

| Elemento | Seletor | Usado em |
|---|---|---|
| Select de cofre | `By.NAME, "uuid-cofre"` | `carregar_cofres`, `selecionar_cofre` |

---

## Modal de upload — envio do arquivo
**Aparece após selecionar cofre**

| Elemento | Seletor | Usado em |
|---|---|---|
| Input de arquivo | `By.ID, "fileupload"` | `upload_documento` |
| Botão "Começar" (IA D4Sign — aparece na 1ª vez) | `By.ID, "botao-analyzer"` | `upload_documento` |
| Modal "Ok, entendi!" (assinatura posicionada — 1ª vez) | `By.CSS_SELECTOR, 'a.btn.btn-primary[href="javascript: fechar_instrucoes();"]'` | `upload_documento` |

**URL após upload bem-sucedido:** `https://secure.d4sign.com.br/desk/viewblob/<uuid>.html`

---

## Página do documento (viewblob)

| Elemento | Seletor | Usado em |
|---|---|---|
| Status "AGUARDANDO SIGNATÁRIOS" | `By.XPATH, "//span[contains(@class,'label-warning') and normalize-space()='AGUARDANDO SIGNATÁRIOS']"` | `upload_documento` (confirmação) |
| Campo e-mail signatário | `By.ID, "email-assinatura"` | `adicionar_email` |
| Botão "Adicionar" | `By.ID, "adicionar-assinatura"` | `adicionar_email` |
| Lista de signatários (confirmação) | `By.ID, "lista-assinatura"` | `adicionar_email` (wait) |
| Checkbox de fluxo | `By.ID, "checkboxFluxo"` | `adicionar_emails` |
| Botão "Enviar para assinatura" | `By.ID, "enviar-para-assinatura"` | `envio_para_assinatura` |
| Editor de mensagem (contenteditable) | `By.CSS_SELECTOR, ".note-editable.card-block[contenteditable='true'][role='textbox']"` | `envio_para_assinatura` |
| Botão salvar/enviar mensagem | `By.ID, "btnSalvarDocumento"` | `envio_para_assinatura` |
