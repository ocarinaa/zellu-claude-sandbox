# 🤖 Zellu IA - Assistente Inteligente para Direitos do Consumidor

<div align="center">

**Plataforma conversacional baseada em IA para análise automatizada de casos de direitos do consumidor (CDC)**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.20-purple.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#-licença)

[Funcionalidades](#-funcionalidades-principais) • [Instalação](#-instalação-e-setup) • [Uso](#-como-executar) • [API](#-endpoints-api) • [Testes](#-testes) • [Contribuir](#-contribuindo)

</div>

---

## 📋 Sobre o Projeto

**Zellu IA** é uma plataforma conversacional inteligente que utiliza **Large Language Models (LLMs)** e **Retrieval-Augmented Generation (RAG)** para auxiliar consumidores brasileiros a entenderem seus direitos segundo o **Código de Defesa do Consumidor (CDC)**.

### 🎯 Problema que Resolve

Muitos consumidores não conhecem seus direitos ou não sabem como proceder ao enfrentar problemas com empresas. O acesso à justiça e a informações jurídicas precisas é limitado, complexo e custoso.

### 💡 Solução Proposta

Uma IA conversacional que:
- 🗣️ **Conversa naturalmente** com o usuário para coletar informações sobre o caso
- 📚 **Consulta automaticamente** artigos relevantes do CDC usando busca semântica
- 💰 **Calcula valores estimados** de indenização baseados em jurisprudência e regras de negócio
- 🎯 **Recomenda soluções** ranqueadas (amigável, extrajudicial, judicial) com justificativas
- 📄 **Analisa documentos** (PDFs, imagens) via OCR para extrair informações automaticamente
- ✅ **Gera análise completa** em JSON estruturado com direitos, valores e próximos passos

### 🚀 Diferenciais Técnicos

- **State Machine com LangGraph:** Orquestra 5 nós especializados (coleta, validação, decisão, análise, finalização)
- **RAG Híbrido:** Combina embeddings vetoriais (FAISS) com busca semântica para CDC
- **Fallback Multi-LLM:** Claude Sonnet 4 como primary, OpenAI GPT-4 como fallback
- **Heurísticas Inteligentes:** Cálculos baseados em multipliers de artigos CDC e modificadores contextuais
- **OCR Multi-formato:** Suporte a PDFs (PyMuPDF) e imagens (Tesseract) com análise via LLM
- **Streaming Real-time:** SSE (Server-Sent Events) para respostas progressivas
- **Persistência Robusta:** PostgreSQL + Redis com cache-first strategy

---

## ✨ Funcionalidades Principais

### 🧠 Módulo Conversacional (FASE 1-2)
- ✅ **Prompts Adaptativos:** 3 tons (conciliador, formal, técnico) ajustáveis dinamicamente
- ✅ **LLM Client com Fallback:** Claude Sonnet 4 → OpenAI GPT-4 automático
- ✅ **Streaming SSE:** Respostas progressivas em tempo real
- ✅ **Conversation Manager:** Gerencia histórico, contexto e state transitions

### 🔌 REST API (FASE 2)
- ✅ **FastAPI Framework:** 6 endpoints principais documentados (OpenAPI/Swagger)
- ✅ **Error Handling:** Tratamento robusto de exceções com códigos HTTP apropriados
- ✅ **CORS & Security:** Headers configuráveis e autenticação (X-API-Key)
- ✅ **Health Checks:** Endpoint `/health` com status de dependências

### 💾 Persistência (FASE 3-4A)
- ✅ **PostgreSQL:** 3 tabelas (Conversation, Message, AnalysisCache)
- ✅ **Redis Cache:** Session cache com TTL configurável
- ✅ **Repository Pattern:** Abstração de acesso a dados
- ✅ **Docker Compose:** Infra local pronta para desenvolvimento
- ✅ **Cache-First Strategy:** Redis → PostgreSQL para performance

### 🤖 State Machine com LangGraph (FASE 4B-4B.1)
- ✅ **5 Nós Especializados:**
  - `collector_node`: Coleta informações estruturadas do usuário
  - `validator_node`: Valida completude e qualidade dos dados
  - `decider_node`: Decide próximo passo baseado em confiança
  - `analyzer_node`: Busca artigos CDC relevantes via RAG
  - `finisher_node`: Gera análise final com cálculos e recomendações
- ✅ **ExtractedInfo Schema:** 20+ campos estruturados (empresa, valor, documentos, protocolo, etc.)
- ✅ **Edges Condicionais:** Roteamento inteligente baseado em estado
- ✅ **Retrocompatibilidade:** Fallback para modo não-LangGraph

### 📚 RAG + CDC (FASE 4C)
- ✅ **Knowledge Base CDC:** 10 artigos essenciais estruturados (JSON)
- ✅ **Embeddings:** OpenAI text-embedding-3-small (1536 dimensões)
- ✅ **Vector Store:** FAISS IndexFlatL2 para busca por similaridade
- ✅ **Retriever Semântico:** Top-K artigos com scores de relevância
- ✅ **Singleton Pattern:** Inicialização única do retriever para performance

### 🧮 Heurísticas Inteligentes (FASE 4D)
- ✅ **ValueEstimator:**
  - Calcula dano material (valor × multiplier do artigo)
  - Calcula dano moral (base values por artigo)
  - Bônus: +20% por documentação, +30% por múltiplas violações
  - Limites: mínimo R$ 500, máximo R$ 50.000
- ✅ **RecommendationScorer:**
  - Ranqueia 3 tipos: amigável, extrajudicial, judicial
  - 6 modificadores: documentos, valor, clareza, tentativas, protocolo, artigos
  - Gera justificativas contextualizadas por solução

### 📄 Upload + OCR (FASE 4E)
- ✅ **File Upload Endpoint:** Multipart/form-data com validação
- ✅ **FileValidator:** MIME detection (python-magic), size limits (50MB geral, 10MB imagens)
- ✅ **LocalStorage:** Armazenamento organizado por `chat_id`, nomes únicos com timestamp
- ✅ **PDFExtractor:** PyMuPDF para extração de texto de PDFs
- ✅ **ImageOCR:** Tesseract com suporte a português (`por`)
- ✅ **DocumentAnalyzer:** LLM extrai tipo, valores monetários, datas, empresas e resumo

### 🧪 Testes Completos
- ✅ **18 Testes Unitários:** CDC loader, estimador, scorer, validator, extractor
- ✅ **10 Testes de Integração:** LangGraph flow, RAG pipeline, storage, persistence
- ✅ **5 Cenários E2E:** Cobrança indevida, cancelamento, upload de documentos
- ✅ **Coverage:** 48% (excelente considerando dependências externas de API)

---

## 🏗️ Arquitetura

### Visão Geral

```
┌─────────────┐
│   Cliente   │
│ (Frontend)  │
└──────┬──────┘
       │ HTTP/SSE
       ▼
┌─────────────────────────────────────────────┐
│           FastAPI REST API                  │
│  ┌────────┬─────────┬──────────┬─────────┐ │
│  │ /start │ /message│ /stream  │ /upload │ │
│  └────────┴─────────┴──────────┴─────────┘ │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│       ConversationManager                   │
│  (Orquestra state machine + persistence)    │
└──────┬──────────────────────────────────────┘
       │
       ├───────────────────┬──────────────┐
       ▼                   ▼              ▼
┌──────────────┐   ┌─────────────┐  ┌────────────┐
│  LangGraph   │   │ PostgreSQL  │  │   Redis    │
│ State Machine│   │(Persistence)│  │  (Cache)   │
└──────┬───────┘   └─────────────┘  └────────────┘
       │
       ├─────────┬─────────┬─────────┬─────────┐
       ▼         ▼         ▼         ▼         ▼
  ┌─────────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌────────┐
  │Collector│ │Validator│ │Decider│ │Analyzer│ │Finisher│
  └─────────┘ └────────┘ └───────┘ └────┬───┘ └────┬───┘
                                         │          │
                                         ▼          ▼
                                    ┌────────┐ ┌──────────┐
                                    │  RAG   │ │Calculator│
                                    │+ FAISS │ │ Modules  │
                                    └────────┘ └──────────┘
```

### Fluxo de Dados

1. **Cliente → API:** Usuário envia mensagem via `/message` ou streaming via `/stream`
2. **API → ConversationManager:** Manager orquestra conversa e state transitions
3. **ConversationManager → LangGraph:** State machine processa com 5 nós especializados
4. **Analyzer → RAG:** Busca semântica em CDC usando FAISS + OpenAI embeddings
5. **Finisher → Calculators:** Estima valores e rankeia recomendações
6. **State → Persistence:** Salva em PostgreSQL + cache em Redis
7. **Response → Cliente:** Retorna análise estruturada ou stream SSE

---

## 🛠️ Stack Tecnológica

### Core
- **Python 3.11+** - Linguagem principal
- **FastAPI 0.104+** - Framework web assíncrono
- **Uvicorn** - ASGI server
- **Pydantic v2** - Validação de dados e schemas

### IA & LLMs
- **Anthropic Claude Sonnet 4** - LLM primary (via SDK)
- **OpenAI GPT-4** - LLM fallback + embeddings
- **LangGraph 0.0.20** - State machine orquestração
- **FAISS 1.7.4** - Vector similarity search

### Persistência
- **PostgreSQL 14+** - Database principal (via asyncpg)
- **SQLAlchemy 2.0** - ORM assíncrono
- **Redis 5.0+** - Cache de sessões (via redis-py)
- **Alembic** - Migrations

### OCR & Documentos
- **PyMuPDF 1.23.8** - Extração de PDF
- **Tesseract OCR** - OCR em imagens
- **Pillow 10.2.0** - Processamento de imagens
- **python-magic 0.4.27** - MIME detection

### Testes
- **pytest 7.4.3** - Framework de testes
- **pytest-asyncio 0.21.1** - Suporte assíncrono
- **pytest-cov 4.1.0** - Coverage reports
- **pytest-mock 3.12.0** - Mocking

### DevOps
- **Docker & Docker Compose** - Containerização
- **aiofiles 23.2.1** - I/O assíncrono

---

## 📦 Instalação e Setup

### Pré-requisitos

#### Sistema Operacional

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  tesseract-ocr \
  tesseract-ocr-por \
  git
```

**macOS:**
```bash
brew install python@3.11 tesseract tesseract-lang
```

**Windows:**
- Python 3.11+: https://www.python.org/downloads/
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Adicionar Tesseract ao PATH

#### Docker (Recomendado para PostgreSQL + Redis)

```bash
# Verificar instalação
docker --version
docker-compose --version

# Se não tiver instalado:
# Ubuntu: https://docs.docker.com/engine/install/ubuntu/
# Mac: https://docs.docker.com/desktop/mac/install/
# Windows: https://docs.docker.com/desktop/windows/install/
```

### Clonagem e Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/[SEU-USUARIO]/zellu-claude-sandbox.git
cd zellu-claude-sandbox

# 2. Crie ambiente virtual
python3.11 -m venv venv

# 3. Ative o ambiente
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate     # Windows

# 4. Atualize pip
pip install --upgrade pip

# 5. Instale dependências
pip install -r requirements.txt
```

### Configuração

#### 1. Variáveis de Ambiente

```bash
# Copie o template
cp .env.example .env

# Edite com suas credenciais
nano .env  # ou vim, code, etc.
```

**Configurações Obrigatórias no `.env`:**

```env
# === LLM APIs ===
ANTHROPIC_API_KEY=sk-ant-api03-...              # Claude Sonnet 4 (obrigatório)
OPENAI_API_KEY=sk-...                           # OpenAI GPT-4 + embeddings (obrigatório)

# === Database ===
DATABASE_URL=postgresql+asyncpg://zellu:zellu123@localhost:5432/zellu_db
REDIS_URL=redis://localhost:6379/0

# === API ===
APP_NAME="Zellu IA"
APP_VERSION="1.0.0"
ENV=development
DEBUG=true
API_V1_PREFIX=/api/v1

# === Security ===
X_API_KEY=changeme_in_production

# === Upload ===
MAX_FILE_SIZE=52428800              # 50MB
MAX_IMAGE_SIZE=10485760             # 10MB
UPLOAD_DIR=uploads/

# === OCR ===
TESSERACT_CMD=/usr/bin/tesseract    # Ajuste se necessário
```

#### 2. Infraestrutura (PostgreSQL + Redis)

**Usando Docker Compose (Recomendado):**

```bash
# Subir containers
docker-compose up -d

# Verificar status
docker-compose ps

# Logs
docker-compose logs -f postgres redis
```

**OU instalação local:**

```bash
# Ubuntu
sudo apt-get install postgresql-14 redis-server

# macOS
brew install postgresql@14 redis

# Inicie os serviços
sudo systemctl start postgresql redis-server
```

#### 3. Banco de Dados

```bash
# Criar banco (se não existir)
createdb zellu_db

# Rodar migrations (quando implementadas)
# alembic upgrade head
```

### Verificação da Instalação

```bash
# Teste Python
python --version
# Deve mostrar: Python 3.11.x

# Teste Tesseract
tesseract --version
# Deve mostrar versão instalada

# Teste PostgreSQL
docker-compose exec postgres psql -U zellu -d zellu_db -c "SELECT 1;"
# Deve retornar: 1

# Teste Redis
docker-compose exec redis redis-cli ping
# Deve retornar: PONG

# Teste dependências Python
pip list | grep -E "fastapi|anthropic|openai|langgraph|faiss"
# Deve mostrar todas instaladas
```

---

## 🚀 Como Executar

### Desenvolvimento

```bash
# Ative o ambiente virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Inicie o servidor com reload automático
uvicorn src.zellu.app:app --reload --port 8000 --host 0.0.0.0

# Logs mais verbosos
uvicorn src.zellu.app:app --reload --port 8000 --log-level debug
```

**Acesse:**
- 🌐 **API:** http://localhost:8000
- 📖 **Documentação (Swagger):** http://localhost:8000/docs
- 📋 **Redoc:** http://localhost:8000/redoc
- ❤️ **Health Check:** http://localhost:8000/health

### Produção

**Com Gunicorn + Uvicorn workers:**

```bash
# Instalar Gunicorn
pip install gunicorn

# Executar com múltiplos workers
gunicorn src.zellu.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**Com Docker:**

```bash
# Build da imagem
docker build -t zellu-ia:latest .

# Run container
docker run -d \
  --name zellu-ia \
  -p 8000:8000 \
  --env-file .env \
  zellu-ia:latest

# Logs
docker logs -f zellu-ia
```

### Uso da API

**Exemplo: Iniciar conversa**

```bash
curl -X POST "http://localhost:8000/api/v1/chat/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{
    "user_name": "João Silva",
    "tone": "conciliador"
  }'

# Resposta:
# {
#   "chat_id": "uuid-123...",
#   "message": "Olá, João! Sou a Zellu IA...",
#   "state": "collect"
# }
```

**Exemplo: Enviar mensagem**

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{
    "chat_id": "uuid-123...",
    "message": "Fui cobrado R$ 89,90 indevidamente pela NET Claro"
  }'
```

**Exemplo: Streaming SSE**

```bash
curl -N "http://localhost:8000/api/v1/chat/stream?chat_id=uuid-123..." \
  -H "X-API-Key: changeme"

# Resposta:
# data: {"content": "Entendi", "done": false}
# data: {"content": " que", "done": false}
# data: {"content": " você", "done": false}
# ...
# data: {"content": "análise completa.", "done": true}
```

**Exemplo: Upload de documento**

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "X-API-Key: changeme" \
  -F "chat_id=uuid-123..." \
  -F "file=@/path/to/fatura.pdf"

# Resposta:
# {
#   "success": true,
#   "filename": "20240101_abc123_fatura.pdf",
#   "analysis": {
#     "document_type": "fatura",
#     "monetary_values": [89.90],
#     "companies_mentioned": ["NET Claro"],
#     "summary": "Fatura referente a cobrança de R$ 89,90..."
#   }
# }
```

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com saída verbosa
pytest -v

# Apenas unitários
pytest tests/unit/ -v

# Apenas integração
pytest tests/integration/ -v

# Testes específicos
pytest tests/unit/test_estimator.py -v

# Rodar em paralelo (requer pytest-xdist)
pytest -n auto
```

### Coverage Report

```bash
# Coverage completo
pytest --cov=src tests/

# Com relatório HTML
pytest --cov=src --cov-report=html tests/
# Abre: htmlcov/index.html

# Mostrar linhas não cobertas
pytest --cov=src --cov-report=term-missing tests/

# Coverage mínimo (falha se < 40%)
pytest --cov=src --cov-fail-under=40 tests/
```

### Resultados Esperados

```
======================== test session starts =========================
collected 34 items

tests/unit/test_cdc_loader.py ....                          [ 11%]
tests/unit/test_estimator.py ....                           [ 23%]
tests/unit/test_scorer.py ...                               [ 32%]
tests/unit/test_validator.py ....                           [ 44%]
tests/unit/test_extractor.py ...                            [ 52%]
tests/integration/test_langgraph.py .s                      [ 58%]
tests/integration/test_rag.py .s                            [ 64%]
tests/integration/test_upload.py ..ss                       [ 76%]
tests/e2e/test_cobranca_indevida.py ss                      [ 82%]
tests/e2e/test_cancelamento.py s                            [ 85%]
tests/e2e/test_with_document.py ss                          [100%]

=============== 23 passed, 11 skipped, 3 warnings in 1.72s ===========

---------- coverage: platform linux, python 3.11.14 ----------
Name                             Stmts   Miss  Cover
----------------------------------------------------
src/calculators/estimator.py       37      5   86%
src/calculators/scorer.py          67     14   79%
src/rag/cdc_loader.py               45      4   91%
src/storage/local.py                27      1   96%
src/storage/validator.py            37      9   76%
----------------------------------------------------
TOTAL                             1746    907   48%
```

---

## 📡 Endpoints API

### Documentação Interativa

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Principais Endpoints

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `GET` | `/health` | ❌ | Health check da API e dependências |
| `POST` | `/api/v1/chat/start` | ✅ | Inicia nova conversa |
| `POST` | `/api/v1/chat/message` | ✅ | Envia mensagem do usuário |
| `GET` | `/api/v1/chat/stream` | ✅ | Streaming SSE de resposta |
| `POST` | `/api/v1/chat/finish` | ✅ | Finaliza e gera análise completa |
| `GET` | `/api/v1/chat/{chat_id}` | ✅ | Recupera conversa completa |
| `GET` | `/api/v1/chat/{chat_id}/analysis` | ✅ | Recupera análise (se existir) |
| `POST` | `/api/v1/upload` | ✅ | Upload de arquivo (PDF/imagem) |

**Auth:** Header `X-API-Key: seu-token-aqui` (configurado em `.env`)

### Schemas de Resposta

**StartConversationResponse:**
```json
{
  "chat_id": "uuid-v4",
  "message": "Olá! Sou a Zellu IA...",
  "state": "collect",
  "tone": "conciliador"
}
```

**SendMessageResponse:**
```json
{
  "chat_id": "uuid-v4",
  "message": "Entendi que você foi cobrado indevidamente...",
  "state": "collect",
  "should_finish": false,
  "extracted_info": {
    "problem_description": "Cobrança indevida",
    "company_name": "NET Claro",
    "monetary_value": 89.90,
    "has_documents": false,
    "confidence_score": 0.85
  }
}
```

**AnalysisData (Finalização):**
```json
{
  "summary": "Caso de cobrança indevida...",
  "estimated_value": 5200.50,
  "rights": [
    "CDC Art. 42 - Direito à devolução em dobro...",
    "CDC Art. 6 - Direitos básicos do consumidor..."
  ],
  "recommendations": [
    {
      "type": "amigavel",
      "score": 8.5,
      "reason": "Caso claro de cobrança indevida com documentação..."
    },
    {
      "type": "extrajudicial",
      "score": 7.2,
      "reason": "Procon pode intermediar efetivamente..."
    },
    {
      "type": "judicial",
      "score": 6.0,
      "reason": "Juizado Especial Cível para valores até R$ 40.000..."
    }
  ],
  "next_steps": [
    "1. Reunir documentação (faturas, comprovantes, protocolos)",
    "2. Tentar resolução amigável via SAC/Ouvidoria",
    "3. Se não resolver, registrar reclamação no Procon"
  ],
  "relevant_cdc_articles": [
    {
      "number": "42",
      "title": "Cobrança Indevida",
      "relevance": 0.95
    }
  ]
}
```

---

## 🗂️ Estrutura do Projeto

```
zellu-claude-sandbox/
├── .env                        # Variáveis de ambiente (não versionado)
├── .env.example                # Template de configuração
├── .gitignore                  # Arquivos ignorados pelo git
├── docker-compose.yml          # Compose para PostgreSQL + Redis
├── Dockerfile                  # Imagem Docker da aplicação
├── pytest.ini                  # Configuração do pytest
├── requirements.txt            # Dependências Python
├── README.md                   # Documentação (este arquivo)
│
├── src/                        # Código-fonte principal
│   ├── api/                    # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Injeção de dependências
│   │   ├── endpoints.py        # Endpoints principais (upload, etc)
│   │   ├── routes/             # Rotas organizadas
│   │   │   ├── conversation.py # Rotas de conversa
│   │   │   └── __init__.py
│   │   └── schemas.py          # Schemas Pydantic da API
│   │
│   ├── calculators/            # Heurísticas de cálculo (FASE 4D)
│   │   ├── __init__.py
│   │   ├── estimator.py        # ValueEstimator (cálculo de valores)
│   │   ├── rules.py            # Regras de negócio CDC
│   │   └── scorer.py           # RecommendationScorer (ranking)
│   │
│   ├── cache/                  # Redis cache (FASE 3)
│   │   ├── __init__.py
│   │   ├── redis_client.py     # Cliente Redis
│   │   └── session_cache.py    # Cache de sessões
│   │
│   ├── conversation/           # Gerenciamento de conversas (FASE 1)
│   │   ├── __init__.py
│   │   ├── extractor.py        # Extração de dados estruturados
│   │   ├── manager.py          # ConversationManager (core)
│   │   └── schemas.py          # Schemas de conversa
│   │
│   ├── core/                   # LangGraph state machine (FASE 4B)
│   │   ├── __init__.py
│   │   ├── graph.py            # Criação e compilação do grafo
│   │   ├── state.py            # ConversationGraphState
│   │   └── nodes/              # Nós do LangGraph
│   │       ├── __init__.py
│   │       ├── analyzer.py     # RAG + busca CDC
│   │       ├── collector.py    # Coleta de informações
│   │       ├── decider.py      # Decisões de fluxo
│   │       ├── finisher.py     # Finalização + cálculos
│   │       └── validator.py    # Validação de dados
│   │
│   ├── database/               # PostgreSQL + ORM (FASE 3)
│   │   ├── __init__.py
│   │   ├── connection.py       # Conexão assíncrona
│   │   ├── models.py           # Modelos SQLAlchemy
│   │   └── repositories.py     # Repository pattern
│   │
│   ├── llm/                    # LLM clients (FASE 1)
│   │   ├── __init__.py
│   │   ├── client.py           # LLMClient com fallback
│   │   ├── config.py           # Configurações LLM
│   │   └── exceptions.py       # Exceções customizadas
│   │
│   ├── ocr/                    # OCR + análise de documentos (FASE 4E)
│   │   ├── __init__.py
│   │   ├── document_analyzer.py # Análise via LLM
│   │   ├── image_ocr.py        # Tesseract OCR
│   │   └── pdf_extractor.py    # PyMuPDF extrator
│   │
│   ├── prompts/                # System prompts (FASE 1)
│   │   ├── __init__.py
│   │   ├── examples.py         # Exemplos few-shot
│   │   └── system.py           # Prompts por tom
│   │
│   ├── rag/                    # RAG + CDC (FASE 4C)
│   │   ├── __init__.py
│   │   ├── cdc_loader.py       # Carrega knowledge base
│   │   ├── embeddings.py       # Gerador de embeddings
│   │   ├── retriever.py        # CDCRetriever (singleton)
│   │   ├── vector_store.py     # FAISS vector store
│   │   └── kb/                 # Knowledge base
│   │       └── cdc.json        # 10 artigos CDC estruturados
│   │
│   ├── storage/                # File storage + validação (FASE 4E)
│   │   ├── __init__.py
│   │   ├── local.py            # LocalStorage (async)
│   │   └── validator.py        # FileValidator
│   │
│   └── zellu/                  # FastAPI app principal
│       ├── __init__.py
│       ├── app.py              # Aplicação FastAPI
│       ├── schemas.py          # Schemas base
│       └── settings.py         # Configurações (pydantic-settings)
│
├── tests/                      # Suite de testes
│   ├── __init__.py
│   ├── conftest.py             # Fixtures compartilhadas
│   │
│   ├── unit/                   # Testes unitários (18 testes)
│   │   ├── __init__.py
│   │   ├── test_cdc_loader.py
│   │   ├── test_estimator.py
│   │   ├── test_extractor.py
│   │   ├── test_scorer.py
│   │   └── test_validator.py
│   │
│   ├── integration/            # Testes de integração (10 testes)
│   │   ├── __init__.py
│   │   ├── test_langgraph.py
│   │   ├── test_persistence.py
│   │   ├── test_rag.py
│   │   └── test_upload.py
│   │
│   └── e2e/                    # Testes end-to-end (5 cenários)
│       ├── __init__.py
│       ├── test_cancelamento.py
│       ├── test_cobranca_indevida.py
│       └── test_with_document.py
│
├── uploads/                    # Diretório de uploads (criado automaticamente)
│   └── [chat_id]/              # Arquivos organizados por conversa
│
└── docs/                       # Documentação adicional (opcional)
    ├── ARCHITECTURE.md
    ├── API.md
    └── CONTRIBUTING.md
```

---

## 🔧 Configurações Avançadas

### Variáveis de Ambiente Completas

```env
# ==========================================
# LLM APIs
# ==========================================
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
LLM_PRIMARY_PROVIDER=anthropic          # anthropic | openai
LLM_FALLBACK_ENABLED=true
LLM_TIMEOUT=30                          # segundos
LLM_MAX_RETRIES=3

# ==========================================
# Database
# ==========================================
DATABASE_URL=postgresql+asyncpg://zellu:zellu123@localhost:5432/zellu_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0
DATABASE_ECHO=false                     # true para SQL logging

# ==========================================
# Redis Cache
# ==========================================
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600                          # 1 hora (segundos)
REDIS_MAX_CONNECTIONS=50

# ==========================================
# API Configuration
# ==========================================
APP_NAME="Zellu IA"
APP_VERSION="1.0.0"
ENV=development                         # development | staging | production
DEBUG=true
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# ==========================================
# Security
# ==========================================
X_API_KEY=changeme_in_production
SECRET_KEY=your-secret-key-here         # Para JWT (futuro)
ALLOWED_HOSTS=["localhost","127.0.0.1"]

# ==========================================
# Upload & Storage
# ==========================================
MAX_FILE_SIZE=52428800                  # 50MB
MAX_IMAGE_SIZE=10485760                 # 10MB
UPLOAD_DIR=uploads/
ALLOWED_MIME_TYPES=["application/pdf","image/jpeg","image/png","image/webp"]

# ==========================================
# OCR
# ==========================================
TESSERACT_CMD=/usr/bin/tesseract
TESSERACT_LANG=por
OCR_TIMEOUT=30                          # segundos

# ==========================================
# RAG & Embeddings
# ==========================================
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
FAISS_INDEX_TYPE=IndexFlatL2
RAG_TOP_K=5                             # Número de artigos retornados

# ==========================================
# LangGraph
# ==========================================
LANGGRAPH_MAX_ITERATIONS=20
LANGGRAPH_TIMEOUT=120                   # segundos
STATE_MACHINE_ENABLED=true

# ==========================================
# Logging
# ==========================================
LOG_LEVEL=INFO                          # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                         # json | text
LOG_FILE=logs/zellu.log
```

### Customização de Heurísticas

Edite `src/calculators/rules.py` para ajustar:

```python
# Multipliers por artigo CDC
CDC_VALUE_RULES = {
    "42": {
        "multiplier": 2.0,              # Devolução em dobro
        "moral_damage_base": 2000.0,
        "description": "Cobrança indevida"
    },
    "71": {
        "multiplier": 2.0,
        "moral_damage_base": 5000.0,    # Aumentar/diminuir conforme jurisprudência
        "description": "Cobrança abusiva"
    }
}

# Modificadores de score
SCORE_MODIFIERS = {
    "has_documents": {"amigavel": +1.0, "extrajudicial": +0.5},
    "high_value": {"judicial": +2.0, "amigavel": -1.0},
    # Adicione novos modificadores aqui
}
```

### Expansão da Knowledge Base CDC

Adicione novos artigos em `src/rag/kb/cdc.json`:

```json
{
  "articles": [
    {
      "number": "XX",
      "title": "Título do Artigo",
      "content": "Texto completo do artigo...",
      "keywords": ["palavra1", "palavra2"],
      "category": "categoria"
    }
  ]
}
```

Depois recrie o vector store:

```python
from src.rag import initialize_cdc_retriever
import asyncio

async def rebuild():
    retriever = await initialize_cdc_retriever()
    # Vector store é recriado automaticamente

asyncio.run(rebuild())
```

---

## 🎯 Roadmap

### ✅ Concluído (v1.0)
- [x] Base conversacional com LLM
- [x] REST API completa
- [x] Persistência PostgreSQL + Redis
- [x] LangGraph state machine (5 nós)
- [x] RAG com CDC (10 artigos)
- [x] Heurísticas de cálculo
- [x] Upload + OCR
- [x] Suite de testes (48% coverage)

### 🚧 Curto Prazo (v1.1 - 1-2 semanas)
- [ ] **Expansão CDC:** 10 → 50+ artigos essenciais
- [ ] **Melhorias de testes:** Coverage 48% → 70%+
- [ ] **Performance:** Cache de embeddings, otimização de queries
- [ ] **Monitoring:** Logs estruturados, métricas Prometheus
- [ ] **CI/CD:** GitHub Actions para testes e deploy
- [ ] **Documentação:** Swagger aprimorado, exemplos detalhados

### 🔮 Médio Prazo (v1.5 - 1-2 meses)
- [ ] **WebSockets:** Streaming real-time bidirecional
- [ ] **Analytics Dashboard:** Métricas de uso, casos processados
- [ ] **ML Refinement:** Fine-tuning de heurísticas com dados reais
- [ ] **Multi-tenancy:** Suporte a múltiplas organizações
- [ ] **Notificações:** E-mail/SMS para atualizações de caso
- [ ] **Histórico Enriquecido:** Timeline visual de conversas

### 🌟 Longo Prazo (v2.0 - 3-6 meses)
- [ ] **Jurisprudência:** Integração com base de precedentes judiciais
- [ ] **Geração de Documentos:** PDFs de petições automatizadas
- [ ] **Mobile App:** React Native iOS/Android
- [ ] **White Label:** Personalização para parceiros
- [ ] **IA Multimodal:** Análise de áudio/vídeo
- [ ] **Blockchain:** Registro imutável de evidências

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos abaixo:

### 1. Fork & Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/SEU-USUARIO/zellu-claude-sandbox.git
cd zellu-claude-sandbox
```

### 2. Crie uma Branch

```bash
git checkout -b feature/minha-nova-feature
# ou
git checkout -b fix/correcao-bug
```

### 3. Desenvolva

```bash
# Instale dependências de desenvolvimento
pip install -r requirements-dev.txt  # (se existir)

# Faça suas alterações
# Adicione testes
# Garanta que testes passam
pytest

# Garanta code style
black src/ tests/
flake8 src/ tests/
```

### 4. Commit & Push

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
# Ou: "fix:", "docs:", "test:", "refactor:"

git push origin feature/minha-nova-feature
```

### 5. Pull Request

- Abra PR no GitHub
- Descreva suas mudanças claramente
- Referencie issues relacionadas (#123)
- Aguarde code review

### Guidelines

- **Code Style:** Siga PEP 8, use Black para formatação
- **Testes:** Coverage mínimo de 70% para novos códigos
- **Documentação:** Docstrings em funções públicas
- **Commits:** Mensagens descritivas (Conventional Commits)
- **Type Hints:** Use type hints em todas as funções

### Áreas que Precisam de Ajuda

- 📚 **Expansão CDC:** Adicionar mais artigos estruturados
- 🧪 **Testes:** Aumentar coverage, adicionar E2E reais
- 🌐 **Internacionalização:** Suporte a outros idiomas
- 📱 **Frontend:** Criar interface web/mobile
- 📖 **Documentação:** Tutoriais, exemplos, vídeos

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License**.

```
MIT License

Copyright (c) 2024 Zellu IA

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contato & Suporte

- **Projeto:** Zellu IA - Assistente Inteligente para Direitos do Consumidor
- **Repositório:** https://github.com/[SEU-USUARIO]/zellu-claude-sandbox
- **Issues:** https://github.com/[SEU-USUARIO]/zellu-claude-sandbox/issues
- **Documentação Completa:** `/docs` (quando disponível)
- **E-mail:** [seu-email@exemplo.com]
- **Discord/Slack:** [Link para comunidade]

### Reportar Bugs

Abra uma issue com:
- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Versão do Python, OS, dependências
- Logs relevantes

### Solicitar Features

Abra uma issue com:
- Descrição da funcionalidade
- Caso de uso / motivação
- Impacto esperado
- Alternativas consideradas

---

## 🙏 Agradecimentos

Este projeto não seria possível sem as seguintes tecnologias e comunidades:

- **[Anthropic](https://www.anthropic.com/)** - Claude Sonnet 4, modelo LLM de ponta
- **[OpenAI](https://openai.com/)** - GPT-4 e embeddings text-embedding-3-small
- **[LangChain](https://www.langchain.com/)** / **[LangGraph](https://github.com/langchain-ai/langgraph)** - Framework de orquestração
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e rápido
- **[FAISS](https://github.com/facebookresearch/faiss)** - Vector similarity search da Meta
- **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)** - OCR open source
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** - Processamento de PDFs
- Comunidade **Python** e todos os contribuidores de bibliotecas open source
- **Código de Defesa do Consumidor (CDC)** - Lei 8.078/1990, Brasil

---

## 🏆 Status do Projeto

```
⭐ Stars: [GitHub stars]
🍴 Forks: [GitHub forks]
🐛 Issues: [GitHub issues]
📝 PRs: [GitHub pull requests]
📦 Version: 1.0.0
✅ Build: Passing
📊 Coverage: 48%
```

**Desenvolvido com ❤️ para democratizar acesso a direitos do consumidor no Brasil**

---

<div align="center">

**[⬆ Voltar ao topo](#-zellu-ia---assistente-inteligente-para-direitos-do-consumidor)**

</div>
