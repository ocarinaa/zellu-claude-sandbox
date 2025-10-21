# ZELLU • Chat Conversacional — #01 Setup & Webhook (Skeleton)

**Stack:** Python 3.11+, FastAPI, Uvicorn, pydantic-settings.
**Segurança:** header `X-API-Key`.
**Endpoints:** `/health`, `/webhook/test`, `/webhook/prod`, `/_debug/routes`.

---

## Como rodar

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Copiar configuração
cp .env.example .env

# Iniciar servidor
uvicorn src.zellu.app:app --reload --port 8000
```

**Servidor:** `http://localhost:8000`
**Docs:** `http://localhost:8000/docs`

---

## Testes

```bash
# Executar testes
pytest -v

# Health check
curl http://localhost:8000/health

# Webhook test (requer X-API-Key)
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{"message":"produto com defeito"}'
```

---

## Docker

```bash
# Build
docker build -t zellu-chat-api:dev .

# Run
docker run -d --name zellu -p 8000:8000 \
  -e X_API_KEY=changeme \
  zellu-chat-api:dev

# Logs
docker logs -f zellu
```

---

## Estrutura

```
.
├── Dockerfile
├── requirements.txt
├── .env.example
├── pytest.ini
├── src/
│   └── zellu/
│       ├── app.py         # FastAPI + endpoints
│       ├── schemas.py     # Pydantic models
│       └── settings.py    # Configurações
└── tests/
    └── test_health.py
```

---

## Endpoints

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/health` | ❌ | Status da API |
| GET | `/_debug/routes` | ❌ | Lista de rotas |
| POST | `/webhook/test` | ✅ | Mock com análise completa |
| POST | `/webhook/prod` | ✅ | Mock production-ready |

**Auth:** Header `X-API-Key` (configurado em `.env`)

---

## Variáveis de ambiente

```env
APP_NAME="ZELLU Chat API"
APP_VERSION="0.1.0"
ENV="local"
X_API_KEY="changeme"
```

Ver `.env.example` para template completo.
