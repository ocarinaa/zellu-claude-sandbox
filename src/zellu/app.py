from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import logging

from .settings import get_settings
from .schemas import WebhookInput, WebhookResponse, AnalysisData, Recommendation
from ..api.routes import conversation, webhook, tickets
from ..api import endpoints
from ..database import init_db
from ..cache import RedisClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hooks."""
    # === STARTUP ===
    logger.info("🚀 Iniciando Zellu IA Service...")

    # Inicializa DB
    try:
        await init_db()
        logger.info("✅ PostgreSQL inicializado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar DB: {e}")

    # Conecta Redis
    try:
        redis = await RedisClient.get_client()
        await redis.ping()
        logger.info("✅ Redis conectado")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Redis: {e}")

    logger.info("✅ Zellu IA Service PRONTO!")

    yield

    # === SHUTDOWN ===
    logger.info("🛑 Encerrando...")

    try:
        await RedisClient.close()
        logger.info("✅ Redis desconectado")
    except Exception as e:
        logger.error(f"❌ Erro ao fechar Redis: {e}")

    logger.info("👋 Service encerrado")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Zellu - Assistente Jurídica com IA Conversacional e Persistência",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if x_api_key is None or x_api_key != settings.X_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

@app.get("/health")
def health():
    return {"ok": True, "name": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.ENV}

@app.post("/webhook/test", response_model=WebhookResponse)
def webhook_test(payload: WebhookInput, _=Depends(require_api_key)):
    mock_analysis = AnalysisData(
        problem=payload.message,
        rights=["troca", "reparo"],
        estimatedValue=1000.0,
        recommendations=[
            Recommendation(option="amigavel", score=6.5, reason="Contato inicial com fornecedor"),
            Recommendation(option="extrajudicial", score=7.5, reason="Notificação formal pode acelerar"),
            Recommendation(option="judicial", score=3.0, reason="Ainda não necessário nesta fase"),
        ]
    )
    return WebhookResponse(
        status="ok-test",
        conv_id="conv_mock_test",
        analysis_data=mock_analysis,
        echo=payload.model_dump(),
    )

@app.post("/webhook/prod", response_model=WebhookResponse)
def webhook_prod(payload: WebhookInput, _=Depends(require_api_key)):
    return WebhookResponse(
        status="ok-prod",
        conv_id="conv_mock_prod",
        analysis_data=None,
        echo=payload.model_dump(),
    )

@app.get("/_debug/routes")
def list_routes():
    return sorted([r.path for r in app.router.routes])


@app.get("/")
async def root():
    return {
        "service": "Zellu IA",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


# === AI Conversation Routes ===
# Rotas antigas (mantidas para retrocompatibilidade)
app.include_router(conversation.router, prefix="/api/v1")

# Rotas novas com persistência
app.include_router(endpoints.router)

# Webhook integration com Zellu App
app.include_router(webhook.router)

# Sistema de Tickets
app.include_router(tickets.router)
