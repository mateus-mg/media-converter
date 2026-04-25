# Plano de CI/CD - media-converter

## Objetivo
Adicionar CI de testes pytest + proteção de branch `main`.

## Status
- [x] Criado em: 2026-04-25
- [x] Autor: OpenCode AI

## Tarefas

### Task 1: Criar `.github/workflows/tests.yml`
- **Trigger**: `push` em `main`, `pull_request`
- **Steps**:
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5` com Python 3.12
  3. Instalar dependências: `pip install -r requirements.txt pytest`
  4. Rodar testes: `pytest tests/ -q`

### Task 2: Configurar Branch Protection
Via `gh api`:
- Requerer 1 review de PR
- Dismiss stale reviews
- Requerer status check `Tests` para passar
- Block force pushes e deletions
- Requerer conversation resolution

### Task 3: Criar `pytest.ini`
Arquivo de configuração do pytest para melhorar descoberta de testes.

## Arquivos Criados/Modificados
| Arquivo | Ação | Status |
|---------|------|--------|
| `.github/workflows/tests.yml` | Criar | Pendente |
| `pytest.ini` | Criar | Pendente |

## Comandos de Configuração

```bash
gh api repos/mateus-mg/media-converter/branches/main/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Tests"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

## Notas
- Projeto usa Python 3.12
- Dependências principais: Pillow, pillow-heif
- Testes existentes: 5 arquivos pytest
- Workflow de docs (`docs.yml`) já existe e continuará funcionando
