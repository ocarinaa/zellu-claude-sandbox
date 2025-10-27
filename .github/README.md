# GitHub Actions CI/CD

Este diretório contém os workflows de CI/CD do projeto Zellu IA.

## 🔧 Workflows Configurados

### 1. `tests.yml` - Pipeline Principal de Testes
**Triggers:** Push e Pull Requests nas branches main, master, develop, claude/**

**O que faz:**
- ✅ Configura PostgreSQL 15 e Redis 7 (services)
- ✅ Instala Python 3.12 e dependências
- ✅ Executa testes unitários com cobertura
- ✅ Executa testes de integração
- ✅ Valida qualidade de código (flake8)
- ✅ Envia relatório de cobertura para Codecov

### 2. `ai-quality-check.yml` - Validação Específica da IA
**Triggers:** Push/PR que modifica arquivos de IA (core, prompts, rag, llm, calculators, conversation)

**O que faz:**
- ✅ Testa State Machine LangGraph
- ✅ Valida RAG e base CDC (60 artigos)
- ✅ Testa heurísticas (estimator + scorer)
- ✅ Verifica estrutura dos prompts
- ✅ Confirma cobertura da base de conhecimento

## 🔑 Secrets Necessários

Configure os seguintes secrets no GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Descrição | Obrigatório |
|-------------|-----------|-------------|
| `OPENAI_API_KEY` | Chave API da OpenAI | ✅ Sim |
| `ANTHROPIC_API_KEY` | Chave API da Anthropic | ⚠️ Recomendado |

### Como adicionar secrets:
1. Acesse: https://github.com/ocarinaa/zellu-claude-sandbox/settings/secrets/actions
2. Clique em "New repository secret"
3. Nome: `OPENAI_API_KEY`
4. Valor: Cole sua chave API
5. Clique em "Add secret"
6. Repita para `ANTHROPIC_API_KEY`

## 📊 Status Badges

Adicione ao README.md principal:

```markdown
![Tests](https://github.com/ocarinaa/zellu-claude-sandbox/actions/workflows/tests.yml/badge.svg)
![AI Quality](https://github.com/ocarinaa/zellu-claude-sandbox/actions/workflows/ai-quality-check.yml/badge.svg)
```

## 🚀 Comandos Locais

Para rodar os mesmos testes localmente:

```bash
# Testes unitários com cobertura
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Testes de integração
pytest tests/integration/ -v

# Validação de código
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
```

## 📈 Próximos Passos

- [ ] Adicionar secrets das APIs no GitHub
- [ ] Adicionar badges ao README principal
- [ ] Configurar Codecov (opcional)
- [ ] Adicionar notificações Slack/Discord (opcional)
- [ ] Configurar deploy automático (futuro)
