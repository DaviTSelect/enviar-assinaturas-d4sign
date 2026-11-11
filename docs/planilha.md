# Formato da Planilha de Signatários

## Colunas obrigatórias

| Coluna | Descrição |
|---|---|
| `nome` | Nome usado para localizar o PDF na pasta. Ex: `davi` encontra `davi.pdf`; `joao silva` encontra `joao_silva.pdf`. |
| `email_favorecido` | E-mail do favorecido (1º signatário). **Obrigatório.** |
| `email_coordenador` | E-mail do coordenador (2º signatário). Pode ficar vazio. |
| `email_diretoria` | E-mail da diretoria (3º signatário). Pode ficar vazio. |

## Regras de correspondência com o arquivo PDF

1. O sistema normaliza o valor de `nome` (remove acentos, caixa baixa, apenas alfanuméricos).
2. Procura na pasta selecionada um `.pdf` cujo nome normalizado seja igual ao de `nome`.
3. Se não encontrar exato, faz busca por tokens: todos os termos de `nome` devem estar presentes no nome do arquivo.
4. Se mais de um arquivo coincidir, lança erro pedindo nome mais específico.

## Colunas de e-mail aceitas pela automação

A lógica aceita qualquer coluna cujo cabeçalho (normalizado) seja:
- `email` ou `e_mail`
- Começar com `email_` → ex: `email_favorecido`, `email_coordenador`, `email_diretoria`
- Padrão numérico → ex: `email1`, `email2`, `email_1`, `email_2`

Os e-mails são adicionados na ordem em que as colunas aparecem na planilha.

## Exemplo

| nome | email_favorecido | email_coordenador | email_diretoria |
|---|---|---|---|
| davi | davi@email.com | coord@empresa.com | dir@empresa.com |
| maria | maria@email.com | | |
| joao silva | joao@email.com | coord2@empresa.com | |

## Regras do arquivo

- Formato: `.xlsx` (Excel)
- Primeira linha: cabeçalhos (exatamente como na tabela acima)
- Coluna `nome_arquivo` não é mais necessária — use `nome` para corresponder ao PDF
- Linhas completamente vazias são ignoradas
- Não adicionar linha de instrução/aviso acima do cabeçalho
