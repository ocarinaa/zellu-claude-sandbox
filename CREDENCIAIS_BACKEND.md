# 🔗 CREDENCIAIS PARA INTEGRAÇÃO - BACKEND

**Data:** 27/10/2025
**Para:** Time de Backend/Frontend
**De:** Dev IA

---

## 📡 URL DA IA (Endpoint para Enviar Mensagens)

```
http://<SERVIDOR_ZELLU_IP>:8000/webhook/chat
```

**Quando a IA for deployada no servidor Zellu, substituir `<SERVIDOR_ZELLU_IP>` pelo IP/domínio real.**

**Exemplos possíveis:**
- `http://147.93.9.113:8000/webhook/chat` (se usar mesmo servidor da infra)
- `http://ia.zellu.com.br/webhook/chat` (se configurar domínio)
- `http://zellu-ia.147.93.9.113.sslip.io:8000/webhook/chat` (se usar sslip.io)

**Protocolo:** HTTP POST
**Content-Type:** application/json

---

## 🔑 API KEY (Para Receber Callbacks)

```
1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798
```

**Uso:** Header `x-api-key`
**Onde usar:** No endpoint do backend que recebe callbacks da IA

---

## 📤 FORMATO DE ENVIO (Backend → IA)

**Endpoint:** `POST http://<SERVIDOR_ZELLU_IP>:8000/webhook/chat`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "id": "uuid-unico-da-mensagem",
  "chat_id": "uuid-da-sessao-do-chat",
  "nome": "Nome do Usuário",
  "message_type": "text",
  "body_message": "Mensagem do usuário aqui",
  "audio": null,
  "files": []
}
```

**Exemplo completo:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "chat_id": "abc-123-def-456",
  "nome": "João Silva",
  "message_type": "text",
  "body_message": "Fui cobrado indevidamente pela operadora",
  "audio": null,
  "files": []
}
```

---

## 📥 FORMATO DE RESPOSTA (IA → Backend via Callback)

**A IA vai chamar o endpoint de vocês:**

**URL configurada no .env:** `ZELLU_WEBHOOK_URL`
**Valor atual:** `http://zellu-ia.147.93.9.113.sslip.io/api/chat/webhook`
**⚠️ IMPORTANTE:** Confirmar se esta URL está correta antes de subir!

**Headers:**
```json
{
  "Content-Type": "application/json",
  "x-api-key": "1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798"
}
```

**Body (durante conversa):**
```json
{
  "chat_id": "abc-123-def-456",
  "message": "Entendo sua frustração. Qual é o nome da operadora?",
  "is_finished": false,
  "message_type": "text",
  "analysis_data": null
}
```

**Body (conversa finalizada):**
```json
{
  "chat_id": "abc-123-def-456",
  "message": "Análise completa! Vou criar seu caso.",
  "is_finished": true,
  "message_type": "text",
  "analysis_data": {
    "problem": "Cobrança indevida de R$ 89,90 por 3 meses na operadora Claro",
    "estimatedValue": 539.40,
    "rights": [
      "CDC Art. 42 - Repetição de indébito em dobro",
      "CDC Art. 6º - Direito à proteção contra práticas abusivas"
    ],
    "recommendations": [
      {
        "type": "amigavel",
        "score": 8.5,
        "reason": "Empresa possui histórico de acordos diretos"
      },
      {
        "type": "extrajudicial",
        "score": 7.0,
        "reason": "Procon tem bons resultados com operadoras"
      }
    ],
    "userInfo": {
      "name": "João Silva",
      "cpf": "123.456.789-00",
      "email": "joao@email.com",
      "phone": "(11) 98765-4321"
    },
    "opposingParty": {
      "name": "Claro S.A.",
      "cnpj": "40.432.544/0001-47"
    },
    "caseDetails": {
      "category": "Telecomunicações",
      "subcategory": "Cobrança Indevida",
      "monetaryValue": 269.70,
      "hasDocuments": false,
      "documents": []
    }
  }
}
```

---

## 🔧 IMPLEMENTAÇÃO NO BACKEND

### 1. Endpoint para Receber Mensagens do Frontend

```typescript
// No backend do site
app.post('/api/chat/send', async (req, res) => {
  const { chatId, userId, message } = req.body;

  // Enviar para IA
  await fetch(process.env.AI_SERVICE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      id: uuidv4(),
      chat_id: chatId,
      nome: await getUserName(userId),
      message_type: 'text',
      body_message: message,
      audio: null,
      files: []
    })
  });

  res.json({ status: 'sent' });
});
```

### 2. Endpoint para Receber Callbacks da IA

```typescript
// No backend do site
app.post('/api/chat/webhook', async (req, res) => {
  // Validar API Key
  const apiKey = req.headers['x-api-key'];
  if (apiKey !== process.env.AI_API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { chat_id, message, is_finished, analysis_data } = req.body;

  // Enviar para frontend via WebSocket
  io.to(chat_id).emit('ai_response', {
    message,
    is_finished,
    analysis_data
  });

  // Se conversa finalizada, criar ticket
  if (is_finished && analysis_data) {
    await createTicket(chat_id, analysis_data);
  }

  res.json({ status: 'ok' });
});
```

**Variáveis de ambiente que o backend precisa:**
```env
AI_SERVICE_URL=http://<SERVIDOR_ZELLU_IP>:8000/webhook/chat
AI_API_KEY=1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798
```

---

## ✅ CHECKLIST DE INTEGRAÇÃO

### Backend precisa fazer:

- [ ] Confirmar URL onde IA será deployada
- [ ] Configurar variáveis de ambiente:
  - `AI_SERVICE_URL` - URL da IA
  - `AI_API_KEY` - Chave para validar callbacks
- [ ] Criar endpoint POST /api/chat/send (recebe do frontend)
- [ ] Implementar envio para IA usando `AI_SERVICE_URL`
- [ ] Criar endpoint POST /api/chat/webhook (recebe callbacks)
- [ ] Validar `x-api-key` no callback endpoint
- [ ] Implementar WebSocket para enviar respostas ao frontend
- [ ] Implementar criação de ticket quando `is_finished: true`

### IA já tem pronto (pronto para deploy):

- [x] Endpoint POST /webhook/chat (recebe mensagens)
- [x] Processamento com LangGraph (5 nodes)
- [x] Sistema de checkpoints (Redis)
- [x] Envio de callbacks assíncronos
- [x] Geração de `analysis_data` completo
- [x] RAG com 60 artigos CDC
- [x] Heurísticas de recomendação
- [x] Upload de documentos com OCR
- [x] Sistema de tickets completo
- [x] 54 testes unitários passando
- [x] Docker Compose pronto (PostgreSQL + Redis)
- [x] Alembic migrations aplicadas
- [x] CI/CD com GitHub Actions

---

## 🚀 DEPLOY DA IA

### Pré-requisitos no servidor:

1. **Docker + Docker Compose** instalado
2. **Python 3.11+** instalado
3. **Git** instalado
4. **Porta 8000** disponível

### Passos para deploy:

```bash
# 1. Clonar repositório no servidor
git clone <repo-url> /opt/zellu-ia
cd /opt/zellu-ia

# 2. Configurar .env
cp .env.example .env
nano .env

# Preencher obrigatoriamente:
# - ANTHROPIC_API_KEY (obtida da Anthropic)
# - ZELLU_WEBHOOK_URL (confirmar com backend)

# 3. Subir infraestrutura
docker-compose up -d

# 4. Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux
# OU
.\venv\Scripts\activate  # Windows

# 5. Instalar dependências
pip install -r requirements.txt

# 6. Aplicar migrations
alembic upgrade head

# 7. Iniciar servidor
uvicorn src.zellu.app:app --host 0.0.0.0 --port 8000

# OU com systemd (produção):
# Criar /etc/systemd/system/zellu-ia.service
# Detalhes em ANALISE_COMPLETA_E_PROXIMOS_PASSOS.md
```

---

## 🧪 TESTAR INTEGRAÇÃO

### Teste 1: Health Check

```bash
curl http://<SERVIDOR_ZELLU_IP>:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "service": "Zellu IA",
  "version": "1.0.0-fase5"
}
```

### Teste 2: Enviar mensagem para IA

```bash
curl -X POST http://<SERVIDOR_ZELLU_IP>:8000/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-001",
    "chat_id": "chat-test-123",
    "nome": "Teste",
    "message_type": "text",
    "body_message": "Fui cobrado indevidamente",
    "audio": null,
    "files": []
  }'
```

**Resposta esperada:**
```json
{
  "status": "processing",
  "chat_id": "chat-test-123"
}
```

### Teste 3: Verificar callback

Verificar nos logs do backend se recebeu callback em:
```
POST /api/chat/webhook
Headers: x-api-key: 1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798
```

---

## 🐛 TROUBLESHOOTING

### Erro: "Connection refused"
**Causa:** Servidor da IA não está rodando
**Solução:** Subir servidor com `uvicorn` ou systemd

### Erro: "401 Unauthorized" no callback
**Causa:** API key incorreta ou ausente
**Solução:** Verificar se `x-api-key` está no header com valor correto

### Erro: "404 Not Found" no callback
**Causa:** Endpoint /api/chat/webhook não existe ou URL errada
**Solução:** Backend criar endpoint ou corrigir `ZELLU_WEBHOOK_URL` no .env da IA

### Mensagens não aparecem no frontend
**Causa:** WebSocket não está emitindo eventos
**Solução:** Verificar implementação do `io.to(chat_id).emit()`

---

## 🚨 IMPORTANTE

1. **Obter ANTHROPIC_API_KEY** antes de subir (bloqueador crítico)
2. **Confirmar ZELLU_WEBHOOK_URL** com time de backend
3. **Nunca expor** a API Key `1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798` publicamente
4. **Sempre validar** `x-api-key` antes de processar callback
5. **Porta 8000** deve estar acessível para o backend

---

## 📞 PRÓXIMOS PASSOS

1. **Dev IA:** Enviar este documento + relatório para chefe
2. **Chefe:** Obter `ANTHROPIC_API_KEY` da Anthropic
3. **DevOps:** Deploy da IA no servidor Zellu
4. **Backend:** Implementar endpoints de integração
5. **Todos:** Testar integração completa

---

**Documento criado:** 27/10/2025
**Versão:** 1.1 (ajustado para deploy em servidor)
**Status:** Pronto para deploy
