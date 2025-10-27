# 🛠️ Stack Tecnológica - Zellu IA

## Visão Geral

A Zellu utiliza uma arquitetura moderna, escalável e baseada em microserviços, com forte ênfase em inteligência artificial e automação.

---

## 🎨 Frontend

### Framework Principal
- **NextJS 14+** - React framework com SSR e SSG
- **React 18+** - Biblioteca de UI
- **TypeScript** - Tipagem estática

### UI/UX
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn/ui** - Componentes reutilizáveis
- **Framer Motion** - Animações
- **Lucide Icons** - Ícones modernos

### Estado e Cache
- **TanStack Query (React Query)** - Gerenciamento de estado assíncrono
- **Zustand** - Estado global leve
- **SWR** - Stale-while-revalidate para cache

### Comunicação
- **Axios** - Cliente HTTP
- **EventSource** - SSE (Server-Sent Events) para streaming

---

## ⚙️ Backend

### Framework e Runtime
- **Python 3.12+** - Linguagem principal
- **FastAPI 0.120+** - Framework web assíncrono
- **Uvicorn** - ASGI server
- **Pydantic 2.x** - Validação de dados

### Inteligência Artificial

#### LLMs
- **OpenAI GPT-4** - Modelo principal de conversação
- **Anthropic Claude 3.5** - Modelo alternativo
- **LangChain 0.3+** - Framework de orchestração
- **LangGraph 0.0.20** - State machines complexas

#### RAG (Retrieval-Augmented Generation)
- **FAISS (Facebook AI Similarity Search)** - Vector store
- **OpenAI Embeddings** - Vetorização de texto
- **NumPy 1.26+** - Manipulação de vetores

#### OCR e Documentos
- **PyMuPDF (fitz) 1.24+** - Extração de texto de PDFs
- **Tesseract OCR 0.3.10** - OCR de imagens
- **Pillow 10.4+** - Processamento de imagens
- **python-magic-bin 0.4.14** - Detecção de MIME types

---

## 💾 Banco de Dados

### Primário
- **PostgreSQL 15+** - Banco relacional principal
  - Conversas
  - Mensagens
  - Usuários (futuro)
  - Tickets (futuro)
  - Empresas (futuro)
  - Advogados (futuro)

### Cache
- **Redis 7+** - Cache em memória
  - Conversas ativas
  - Sessões de usuário
  - Rate limiting
  - Filas de background jobs

### ORM
- **SQLAlchemy 2.0.23** - ORM assíncrono
- **AsyncPG 0.29.0** - Driver PostgreSQL assíncrono
- **Alembic 1.13.1** - Migrações de banco

---

## 🔗 Integrações Externas

### Validações e Dados
| Serviço | Uso | Status |
|---------|-----|--------|
| **ViaCEP** | Busca de endereços por CEP | ✅ Implementado |
| **HUB Desenvolvedor** | Validação CPF/CNPJ | 🔄 Planejado |
| **JUDIT** | Validação OAB, consulta processos | 🔄 Planejado |

### Documentação e Assinatura
| Serviço | Uso | Status |
|---------|-----|--------|
| **Autentique** | Assinatura digital de documentos | 🔄 Planejado |

### Pagamentos
| Serviço | Uso | Status |
|---------|-----|--------|
| **Pagar.me** | Assinaturas, pagamentos, créditos | 🔄 Planejado |

### Comunicação
| Serviço | Uso | Status |
|---------|-----|--------|
| **WhatsApp Business API** | Chat automatizado | 🔄 Planejado |
| **Twilio** | Telefonia e SMS | 🔄 Planejado |
| **ElevenLabs** | Voice AI (bot de voz) | 🔄 Planejado |
| **SendGrid / Resend** | E-mails transacionais | 🔄 Planejado |

### Órgãos e Plataformas
| Serviço | Uso | Status |
|---------|-----|--------|
| **Gov.br (Consumidor.gov.br)** | Abertura de chamados | 🔄 Planejado |
| **Reclame Aqui API** | Reputação empresas | 🔄 Planejado |

---

## 🏗️ Infraestrutura

### Hospedagem (Produção)
- **AWS** - Cloud provider principal
  - EC2 para servidores
  - RDS para PostgreSQL
  - ElastiCache para Redis
  - S3 para armazenamento de arquivos
  - CloudFront para CDN

### Hospedagem (Desenvolvimento)
- **VPS Parks + Coolify** - Ambiente de staging
- **Supabase** - Banco de desenvolvimento

### Container e Orquestração
- **Docker** - Containerização
- **Docker Compose** - Orquestração local
- **GitHub Actions** - CI/CD

### Monitoramento e Logs
- **Sentry** - Error tracking (planejado)
- **DataDog / New Relic** - APM (planejado)
- **Grafana + Prometheus** - Métricas (planejado)

---

## 🔐 Segurança

### Autenticação e Autorização
- **JWT (JSON Web Tokens)** - Sessões stateless
- **bcrypt** - Hashing de senhas
- **OAuth 2.0** - Login social (futuro)
- **2FA** - Autenticação de dois fatores (futuro)

### Proteção de Dados
- **HTTPS/TLS** - Criptografia em trânsito
- **Encryption at rest** - Criptografia em repouso (dados sensíveis)
- **LGPD Compliance** - Conformidade legal

### Rate Limiting e Proteção
- **Redis** - Rate limiting
- **CORS** - Controle de origem
- **Helmet.js** - Headers de segurança
- **SQL Injection Protection** - Via SQLAlchemy ORM

---

## 📦 Dependências Python (requirements.txt)

### Web Framework
```
fastapi==0.120.0
uvicorn[standard]
pydantic==2.12.3
pydantic-settings==2.11.0
python-dotenv==1.2.1
httpx==0.28.1
sse-starlette==3.0.2
```

### IA e ML
```
anthropic
openai==2.6.1
langgraph==0.0.20
faiss-cpu==1.12.0
numpy==1.26.4
```

### Banco de Dados
```
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.13.1
redis[hiredis]==5.0.1
```

### Documentos e OCR
```
PyMuPDF==1.24.13
pytesseract==0.3.10
Pillow==10.4.0
python-magic-bin==0.4.14
```

### Upload e Storage
```
aiofiles==23.2.1
python-multipart==0.0.6
```

### Testes
```
pytest==8.3.3
pytest-asyncio==0.23.8
pytest-cov==4.1.0
pytest-mock==3.12.0
```

---

## 🌐 Domínios

### Produção
- **zellu.com.br** - Site institucional
- **app.zellu.com.br** - Aplicação web
- **api.zellu.com.br** - API backend

### Alternativo/Backup
- **zellu.club** - Domínio alternativo para microserviços

---

## 📊 Arquitetura de Dados

### Modelo Atual (Implementado)

```sql
-- Conversas
conversations (
  id: UUID PK,
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP,
  metadata: JSONB
)

-- Mensagens
messages (
  id: UUID PK,
  conversation_id: UUID FK,
  role: ENUM('user', 'assistant'),
  content: TEXT,
  created_at: TIMESTAMP
)

-- Informações Extraídas
extracted_info (
  id: UUID PK,
  conversation_id: UUID FK,
  problem_description: TEXT,
  monetary_value: DECIMAL,
  has_documents: BOOLEAN,
  previous_attempts: JSONB,
  created_at: TIMESTAMP
)
```

### Modelo Futuro (Planejado)

```sql
-- Usuários
users (
  id: UUID PK,
  email: VARCHAR UNIQUE,
  password_hash: VARCHAR,
  user_type: ENUM('cliente', 'empresa', 'advogado'),
  created_at: TIMESTAMP
)

-- Tickets
tickets (
  id: UUID PK,
  conversation_id: UUID FK,
  user_id: UUID FK,
  company_id: UUID FK NULL,
  lawyer_id: UUID FK NULL,
  status: ENUM('aberto', 'em_andamento', 'resolvido', 'encerrado'),
  solution_type: ENUM('amigavel', 'extrajudicial', 'judicial'),
  created_at: TIMESTAMP,
  deadline: TIMESTAMP NULL
)

-- Empresas
companies (
  id: UUID PK,
  cnpj: VARCHAR UNIQUE,
  name: VARCHAR,
  reputation_level: ENUM('bronze', 'prata', 'ouro', 'diamante'),
  created_at: TIMESTAMP
)

-- Advogados
lawyers (
  id: UUID PK,
  user_id: UUID FK,
  oab_number: VARCHAR,
  oab_state: VARCHAR,
  specialties: JSONB,
  credits: INTEGER,
  rating: DECIMAL,
  created_at: TIMESTAMP
)

-- Documentos
documents (
  id: UUID PK,
  ticket_id: UUID FK,
  file_path: VARCHAR,
  file_type: VARCHAR,
  created_at: TIMESTAMP
)
```

---

## 🔄 Fluxo de Dados

### Chat Conversacional
```
Cliente
  ↓ WebSocket/SSE
FastAPI
  ↓ LangGraph
State Machine (5 nodes)
  ↓ LangChain
OpenAI/Anthropic
  ↓ RAG
FAISS (CDC)
  ↓ Heuristics
ValueEstimator + RecommendationScorer
  ↓ Persistence
PostgreSQL + Redis
  ↓ Response Stream
Cliente
```

### Upload de Documentos
```
Cliente
  ↓ Multipart Form Data
FastAPI /upload
  ↓ Validation
FileValidator
  ↓ Storage
LocalStorage (futuro: S3)
  ↓ OCR
PyMuPDF / Tesseract
  ↓ Analysis
Integrate with Conversation
```

---

## 🚀 Performance e Escalabilidade

### Otimizações Implementadas
- ✅ Async/await em todo backend
- ✅ Connection pooling (PostgreSQL)
- ✅ Cache Redis para conversas ativas
- ✅ FAISS para busca vetorial eficiente
- ✅ Streaming de respostas (SSE)

### Otimizações Planejadas
- 🔄 CDN para assets estáticos
- 🔄 Lazy loading de componentes
- 🔄 Database indexing otimizado
- 🔄 Query optimization
- 🔄 Horizontal scaling com load balancer
- 🔄 Background jobs com Celery/RQ

### Limites Atuais
- **Usuários simultâneos:** ~100 (dev)
- **Requisições/segundo:** ~50 (dev)
- **Tamanho upload:** 10 MB
- **Conversas ativas:** Ilimitadas (Redis auto-evict)

### Limites Planejados (Produção)
- **Usuários simultâneos:** 10.000+
- **Requisições/segundo:** 1.000+
- **Tamanho upload:** 50 MB
- **SLA uptime:** 99.9%

---

## 🔧 Ferramentas de Desenvolvimento

### IDE e Editores
- **VSCode** - IDE principal
- **Claude Code** - AI coding assistant

### Controle de Versão
- **Git** - VCS
- **GitHub** - Repositório e CI/CD

### Testes e QA
- **pytest** - Framework de testes
- **pytest-asyncio** - Testes assíncronos
- **pytest-cov** - Cobertura de código
- **pytest-mock** - Mocking

### Linting e Formatação
- **Black** - Code formatter (planejado)
- **isort** - Import sorting (planejado)
- **Flake8** - Linting (planejado)
- **MyPy** - Type checking (planejado)

---

## 📈 Custos Estimados (Mensal)

### Infraestrutura
| Serviço | Custo |
|---------|-------|
| AWS (EC2 + RDS + S3) | $200-500 |
| Redis Cloud | $50-100 |
| Domain + CDN | $20-50 |

### APIs e Serviços
| Serviço | Custo |
|---------|-------|
| OpenAI API | $500-2.000 (depende uso) |
| Anthropic API | $300-1.000 (depende uso) |
| Autentique | $100-300 |
| WhatsApp API | $100-500 |
| SendGrid | $50-200 |

**Total estimado:** $1.320 - $4.650/mês

---

**Última atualização:** Janeiro 2025
**Revisão:** Trimestral ou quando adicionar nova tecnologia
