# 🎫 FASE 5: Sistema de Tickets - Plano de Implementação

**Prioridade:** 🔥 CRÍTICA - Pré-requisito para todas as features futuras
**Tempo Estimado:** 2-3 semanas
**Status:** ⏳ Planejado

---

## 🎯 Objetivo

Implementar um sistema completo de **tickets/chamados** que permita:
1. Criar tickets a partir de conversações
2. Gerenciar estados do ticket (aberto, em_andamento, resolvido, encerrado)
3. Associar tickets a tipos de solução (amigável, extrajudicial, judicial)
4. Rastrear timeline de eventos
5. Acompanhar prazos e SLAs
6. Base para workflow de escalação entre soluções

---

## 📊 Modelo de Dados

### Tabela: `tickets`

```sql
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relacionamentos
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NULL,  -- Futuro: FK para users table
    company_id UUID NULL,  -- Futuro: FK para companies table
    lawyer_id UUID NULL,  -- Futuro: FK para lawyers table

    -- Informações do Ticket
    ticket_number VARCHAR(20) UNIQUE NOT NULL,  -- Ex: "ZLU-2025-001234"
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,

    -- Status e Tipo
    status VARCHAR(50) NOT NULL DEFAULT 'aberto',
        -- CHECK (status IN ('aberto', 'em_andamento', 'resolvido', 'encerrado'))
    solution_type VARCHAR(50) NOT NULL,
        -- CHECK (solution_type IN ('amigavel', 'extrajudicial', 'judicial'))

    -- Valores
    estimated_value DECIMAL(10, 2) NULL,
    final_value DECIMAL(10, 2) NULL,

    -- Prazos
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deadline TIMESTAMP NULL,  -- Prazo para resposta/ação
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Indices
    INDEX idx_tickets_conversation (conversation_id),
    INDEX idx_tickets_status (status),
    INDEX idx_tickets_solution_type (solution_type),
    INDEX idx_tickets_created_at (created_at DESC),
    INDEX idx_tickets_deadline (deadline)
);
```

### Tabela: `ticket_events`

```sql
CREATE TABLE ticket_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,

    -- Evento
    event_type VARCHAR(50) NOT NULL,
        -- Ex: 'status_changed', 'deadline_set', 'message_sent', 'document_uploaded'
    event_data JSONB NOT NULL,
    description TEXT NULL,

    -- Autor
    actor_type VARCHAR(50) NULL,  -- 'system', 'user', 'company', 'lawyer'
    actor_id UUID NULL,

    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indices
    INDEX idx_ticket_events_ticket (ticket_id),
    INDEX idx_ticket_events_type (event_type),
    INDEX idx_ticket_events_created (created_at DESC)
);
```

### Enum: `TicketStatus`

```python
from enum import Enum

class TicketStatus(str, Enum):
    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    RESOLVIDO = "resolvido"
    ENCERRADO = "encerrado"
```

### Enum: `SolutionType`

```python
class SolutionType(str, Enum):
    AMIGAVEL = "amigavel"
    EXTRAJUDICIAL = "extrajudicial"
    JUDICIAL = "judicial"
```

### Enum: `TicketEventType`

```python
class TicketEventType(str, Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    SOLUTION_ESCALATED = "solution_escalated"
    DEADLINE_SET = "deadline_set"
    DEADLINE_REACHED = "deadline_reached"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    DOCUMENT_UPLOADED = "document_uploaded"
    AGREEMENT_PROPOSED = "agreement_proposed"
    AGREEMENT_SIGNED = "agreement_signed"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
```

---

## 🏗️ Estrutura de Arquivos

```
src/
├── tickets/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── service.py          # Business logic
│   ├── repository.py       # Database operations
│   └── utils.py            # Helper functions (ticket number generation)
│
├── api/
│   └── routes/
│       └── tickets.py      # FastAPI routes
│
└── database/
    └── migrations/
        └── versions/
            └── XXXX_add_tickets_tables.py  # Alembic migration
```

---

## 📝 Schemas Pydantic

### `TicketCreate`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class TicketCreate(BaseModel):
    conversation_id: str = Field(..., description="ID da conversação que originou o ticket")
    title: str = Field(..., max_length=255, description="Título resumido do problema")
    description: str = Field(..., description="Descrição completa do caso")
    solution_type: SolutionType = Field(..., description="Tipo de solução escolhida")
    estimated_value: Optional[Decimal] = Field(None, ge=0, description="Valor estimado do caso")
    deadline: Optional[datetime] = Field(None, description="Prazo para ação")
    metadata: dict = Field(default_factory=dict)
```

### `TicketUpdate`

```python
class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    solution_type: Optional[SolutionType] = None
    estimated_value: Optional[Decimal] = Field(None, ge=0)
    final_value: Optional[Decimal] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    metadata: Optional[dict] = None
```

### `TicketResponse`

```python
class TicketResponse(BaseModel):
    id: str
    ticket_number: str
    conversation_id: str
    title: str
    description: str
    status: TicketStatus
    solution_type: SolutionType
    estimated_value: Optional[Decimal]
    final_value: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    metadata: dict

    # Relations
    user_id: Optional[str]
    company_id: Optional[str]
    lawyer_id: Optional[str]

    class Config:
        from_attributes = True
```

### `TicketEventCreate`

```python
class TicketEventCreate(BaseModel):
    ticket_id: str
    event_type: TicketEventType
    event_data: dict
    description: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
```

### `TicketEventResponse`

```python
class TicketEventResponse(BaseModel):
    id: str
    ticket_id: str
    event_type: TicketEventType
    event_data: dict
    description: Optional[str]
    actor_type: Optional[str]
    actor_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

### `TicketListResponse`

```python
class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
```

---

## 🔧 Service Layer (`service.py`)

### Principais Métodos

```python
class TicketService:
    def __init__(self, db: Session, cache: Redis):
        self.repo = TicketRepository(db)
        self.event_repo = TicketEventRepository(db)
        self.cache = cache

    async def create_ticket(self, data: TicketCreate) -> TicketResponse:
        """Cria um novo ticket e registra evento de criação."""

    async def get_ticket(self, ticket_id: str) -> TicketResponse:
        """Busca ticket por ID (com cache)."""

    async def get_ticket_by_number(self, ticket_number: str) -> TicketResponse:
        """Busca ticket por número (ex: ZLU-2025-001234)."""

    async def list_tickets(
        self,
        status: Optional[TicketStatus] = None,
        solution_type: Optional[SolutionType] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> TicketListResponse:
        """Lista tickets com filtros e paginação."""

    async def update_ticket_status(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        actor_id: Optional[str] = None
    ) -> TicketResponse:
        """Atualiza status e registra evento."""

    async def escalate_solution(
        self,
        ticket_id: str,
        new_solution_type: SolutionType,
        reason: str
    ) -> TicketResponse:
        """Escalona ticket para próximo tipo de solução."""

    async def set_deadline(
        self,
        ticket_id: str,
        deadline: datetime,
        reason: str
    ) -> TicketResponse:
        """Define ou atualiza prazo do ticket."""

    async def resolve_ticket(
        self,
        ticket_id: str,
        final_value: Optional[Decimal] = None,
        resolution_notes: str = ""
    ) -> TicketResponse:
        """Marca ticket como resolvido."""

    async def close_ticket(self, ticket_id: str) -> TicketResponse:
        """Encerra ticket (sem resolução)."""

    async def reopen_ticket(self, ticket_id: str, reason: str) -> TicketResponse:
        """Reabre ticket encerrado."""

    async def get_ticket_timeline(self, ticket_id: str) -> list[TicketEventResponse]:
        """Retorna timeline completa de eventos do ticket."""

    async def add_event(self, event: TicketEventCreate) -> TicketEventResponse:
        """Adiciona evento à timeline do ticket."""
```

---

## 🛣️ API Routes (`api/routes/tickets.py`)

### Endpoints

```python
router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    """Cria um novo ticket a partir de uma conversação."""

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Busca ticket por ID."""

@router.get("/number/{ticket_number}", response_model=TicketResponse)
async def get_ticket_by_number(ticket_number: str, db: Session = Depends(get_db)):
    """Busca ticket por número (ex: ZLU-2025-001234)."""

@router.get("/", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[TicketStatus] = None,
    solution_type: Optional[SolutionType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista tickets com filtros e paginação."""

@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    data: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza informações do ticket."""

@router.post("/{ticket_id}/status", response_model=TicketResponse)
async def update_status(
    ticket_id: str,
    new_status: TicketStatus,
    db: Session = Depends(get_db)
):
    """Atualiza status do ticket."""

@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
async def escalate_ticket(
    ticket_id: str,
    new_solution_type: SolutionType,
    reason: str = Body(...),
    db: Session = Depends(get_db)
):
    """Escalona ticket para próximo tipo de solução."""

@router.post("/{ticket_id}/resolve", response_model=TicketResponse)
async def resolve_ticket(
    ticket_id: str,
    final_value: Optional[Decimal] = None,
    resolution_notes: str = Body(""),
    db: Session = Depends(get_db)
):
    """Marca ticket como resolvido."""

@router.post("/{ticket_id}/close", response_model=TicketResponse)
async def close_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Encerra ticket sem resolução."""

@router.post("/{ticket_id}/reopen", response_model=TicketResponse)
async def reopen_ticket(
    ticket_id: str,
    reason: str = Body(...),
    db: Session = Depends(get_db)
):
    """Reabre ticket encerrado."""

@router.get("/{ticket_id}/timeline", response_model=list[TicketEventResponse])
async def get_ticket_timeline(ticket_id: str, db: Session = Depends(get_db)):
    """Retorna timeline completa de eventos."""

@router.post("/{ticket_id}/events", response_model=TicketEventResponse, status_code=201)
async def add_ticket_event(
    ticket_id: str,
    event: TicketEventCreate,
    db: Session = Depends(get_db)
):
    """Adiciona evento à timeline."""
```

---

## 🧪 Testes

### Testes Unitários (`tests/unit/test_ticket_service.py`)

```python
def test_create_ticket(db_session):
    """Testa criação de ticket."""

def test_generate_ticket_number():
    """Testa geração de número único de ticket."""

def test_update_ticket_status(db_session):
    """Testa mudança de status."""

def test_escalate_solution(db_session):
    """Testa escalação amigavel → extrajudicial → judicial."""

def test_resolve_ticket(db_session):
    """Testa resolução de ticket."""

def test_ticket_timeline(db_session):
    """Testa registro de eventos na timeline."""
```

### Testes de Integração (`tests/integration/test_ticket_endpoints.py`)

```python
async def test_create_ticket_endpoint(client):
    """Testa POST /api/tickets/."""

async def test_list_tickets_with_filters(client):
    """Testa GET /api/tickets/ com filtros."""

async def test_ticket_status_flow(client):
    """Testa fluxo aberto → em_andamento → resolvido."""

async def test_ticket_escalation_flow(client):
    """Testa fluxo amigavel → extrajudicial → judicial."""
```

---

## 📋 Checklist de Implementação

### Semana 1: Base de Dados e Models

- [ ] Criar migration Alembic para tabelas `tickets` e `ticket_events`
- [ ] Implementar SQLAlchemy models (`Ticket`, `TicketEvent`)
- [ ] Criar Pydantic schemas (Create, Update, Response)
- [ ] Implementar enums (`TicketStatus`, `SolutionType`, `TicketEventType`)
- [ ] Testar migrations up/down
- [ ] Adicionar seed data para testes

### Semana 2: Service Layer e Repository

- [ ] Implementar `TicketRepository` (CRUD básico)
- [ ] Implementar `TicketEventRepository`
- [ ] Implementar `TicketService` com lógica de negócio
- [ ] Implementar geração de `ticket_number` único
- [ ] Implementar cálculo de prazos (7 dias, 15 dias, etc.)
- [ ] Implementar regras de transição de status
- [ ] Implementar regras de escalação
- [ ] Escrever testes unitários (>80% cobertura)

### Semana 3: API e Integração

- [ ] Implementar rotas FastAPI
- [ ] Integrar com conversação existente
- [ ] Adicionar validações e tratamento de erros
- [ ] Implementar cache Redis para tickets ativos
- [ ] Escrever testes de integração
- [ ] Documentar endpoints (OpenAPI/Swagger)
- [ ] Testar fluxos E2E completos
- [ ] Code review e ajustes finais

---

## 🔗 Integração com Sistema Existente

### Criar Ticket ao Finalizar Conversação

```python
# Em src/conversation/nodes.py - node finisher

async def create_ticket_from_conversation(
    conversation_id: str,
    extracted_info: ExtractedInfo,
    recommendation: dict
) -> str:
    """Cria ticket após conversação finalizada."""

    ticket_data = TicketCreate(
        conversation_id=conversation_id,
        title=f"Caso: {extracted_info.problem_description[:100]}",
        description=extracted_info.problem_description,
        solution_type=recommendation["recommended_solution"],
        estimated_value=recommendation["estimated_value"],
        deadline=calculate_deadline(recommendation["recommended_solution"]),
        metadata={
            "cdc_articles": recommendation["relevant_articles"],
            "confidence_score": recommendation["confidence_score"]
        }
    )

    ticket = await ticket_service.create_ticket(ticket_data)
    return ticket.ticket_number
```

---

## 🎯 Regras de Negócio

### Prazos por Tipo de Solução

| Solução | Prazo Inicial | Ação Automática |
|---------|---------------|-----------------|
| **Amigável** | 7 dias | Notificar cliente se sem resposta |
| **Extrajudicial** | 15 dias | Recomendar escalação judicial |
| **Judicial** | N/A | Gerenciado por advogado |

### Transições de Status Permitidas

```
aberto → em_andamento → resolvido
aberto → encerrado
em_andamento → resolvido
em_andamento → encerrado
resolvido → encerrado
encerrado → aberto (reopen)
```

### Escalação de Solução

```
amigavel → extrajudicial → judicial
```

**Não é permitido:**
- ❌ Retroceder (judicial → extrajudicial)
- ❌ Pular etapas (amigavel → judicial direto) - exceto por solicitação explícita do cliente

---

## 📊 Métricas e KPIs

Campos calculados para analytics:

```python
# Tempo de resolução
resolution_time = resolved_at - created_at

# Taxa de resolução por solução
resolution_rate_by_type = (resolved / total) GROUP BY solution_type

# Taxa de escalação
escalation_rate = (escalated / total)

# Tickets próximos ao prazo
tickets_near_deadline = WHERE deadline < NOW() + INTERVAL '2 days'

# Tickets atrasados
overdue_tickets = WHERE deadline < NOW() AND status IN ('aberto', 'em_andamento')
```

---

## 🚀 Próximos Passos Após FASE 5

Com o sistema de tickets implementado, poderemos prosseguir para:

1. **FASE 6.1:** Workflow Solução Amigável
   - Integrar envio de e-mails automatizados
   - Follow-ups estruturados
   - Sistema de negociação

2. **FASE 6.2:** Workflow Solução Extrajudicial
   - Geração de notificação extrajudicial
   - Integração com Autentique

3. **FASE 6.3:** Workflow Solução Judicial
   - Marketplace de advogados
   - Sistema de captura de casos

---

## 📝 Notas de Implementação

### Geração de Ticket Number

```python
def generate_ticket_number() -> str:
    """Gera número único no formato ZLU-YYYY-NNNNNN."""
    year = datetime.now().year

    # Buscar último número do ano
    last_ticket = db.query(Ticket)\
        .filter(Ticket.ticket_number.like(f"ZLU-{year}-%"))\
        .order_by(Ticket.ticket_number.desc())\
        .first()

    if last_ticket:
        last_num = int(last_ticket.ticket_number.split('-')[-1])
        next_num = last_num + 1
    else:
        next_num = 1

    return f"ZLU-{year}-{next_num:06d}"
```

### Cache Strategy

```python
# Cache ticket por 5 minutos
cache_key = f"ticket:{ticket_id}"
cached = await redis.get(cache_key)

if cached:
    return TicketResponse.parse_raw(cached)

ticket = await db.query(Ticket).get(ticket_id)
await redis.setex(cache_key, 300, ticket.json())
return ticket
```

---

**Documento criado em:** Janeiro 2025
**Responsável:** Equipe de desenvolvimento
**Revisão:** Após conclusão da implementação
