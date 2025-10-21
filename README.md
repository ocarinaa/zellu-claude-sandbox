# ZELLU • Chat Conversacional — #01 Setup & Webhook (Skeleton)
Esqueleto mínimo FastAPI com:
- `/health`
- `/webhook/test` (mock, requer `X-API-Key`)
- `/webhook/prod` (mock, requer `X-API-Key`)
- `/_debug/routes`

## Rodando (terminal integrado)
python -m venv .venv
source .venv/bin/activate || .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn src.zellu.app:app --reload --port 8000
