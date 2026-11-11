# Como Contribuir

## Configurar Ambiente

```powershell
git clone https://github.com/DaviTSelect/enviar-assinaturas-d4sign.git
cd enviar-assinaturas-d4sign

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requeriments.txt

cp .env.example .env
# Preencher .env com credenciais D4Sign
```

## Executar

```powershell
python main.py
```

## Convenção de Commits

| Prefixo | Uso |
|---------|-----|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Documentação |
| `chore:` | Manutenção, dependências |

## Regras

- Nunca commitar `.env` com credenciais reais
- Nunca commitar `Pasta1.xlsx` com dados reais de usuários
- Nunca commitar `venv/`, `logs/`, `__pycache__/`
