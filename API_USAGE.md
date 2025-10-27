# 🚀 Zellu AI - API Usage Guide

Guia completo de uso da API de conversação da Zellu.

---

## 📦 Iniciar o Servidor

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite .env e adicione suas API keys:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Iniciar servidor
uvicorn src.zellu.app:app --reload --port 8000
```

A API estará disponível em: `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

---

## 🎯 Endpoints Disponíveis

### 1️⃣ Iniciar Conversa

**Endpoint:** `POST /api/v1/conversations`

**Request:**
```json
{
  "tone": "conciliador"
}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "tone": "conciliador",
  "created_at": "2024-01-15T10:30:00",
  "message": "Conversa iniciada com sucesso"
}
```

**Opções de `tone`:**
- `"conciliador"` - Amigável e empático (padrão)
- `"formal"` - Profissional e respeitoso
- `"tecnico"` - Técnico-jurídico

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"tone": "conciliador"}'
```

---

### 2️⃣ Enviar Mensagem (Non-Streaming)

**Endpoint:** `POST /api/v1/conversations/{conversation_id}/messages`

**Request:**
```json
{
  "message": "Fui cobrado indevidamente pela operadora",
  "stream": false
}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Entendo sua frustração 😔 Cobrança indevida é um problema comum. Para te ajudar melhor, qual operadora te cobrou?",
  "is_finalized": false,
  "message_count": 2
}
```

**Exemplo cURL:**
```bash
CONV_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST http://localhost:8000/api/v1/conversations/$CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Fui cobrado indevidamente pela operadora",
    "stream": false
  }'
```

---

### 3️⃣ Enviar Mensagem (Streaming via SSE)

**Endpoint:** `POST /api/v1/conversations/{conversation_id}/messages`

**Request:**
```json
{
  "message": "Foi a NET Claro",
  "stream": true
}
```

**Response:** Server-Sent Events (SSE)

```
event: message
data: Entendo

event: message
data:  sua

event: message
data:  frustração

event: done
data: {"is_finalized": false, "message_count": 4}
```

**Exemplo Python:**
```python
import requests
import json

CONV_ID = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/v1/conversations/{CONV_ID}/messages"

response = requests.post(
    url,
    json={"message": "Foi a NET Claro", "stream": True},
    stream=True,
    headers={"Accept": "text/event-stream"}
)

for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            data = decoded[6:]  # Remove 'data: '
            print(data, end='', flush=True)
```

**Exemplo JavaScript (EventSource):**
```javascript
const convId = "550e8400-e29b-41d4-a716-446655440000";

fetch(`/api/v1/conversations/${convId}/messages`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: "Foi a NET Claro",
    stream: true
  })
}).then(response => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  function read() {
    reader.read().then(({done, value}) => {
      if (done) return;

      const chunk = decoder.decode(value);
      console.log(chunk);

      read();
    });
  }

  read();
});
```

---

### 4️⃣ Obter Conversa Completa

**Endpoint:** `GET /api/v1/conversations/{conversation_id}`

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "tone": "conciliador",
  "is_finalized": false,
  "message_count": 4,
  "messages": [
    {
      "role": "user",
      "content": "Fui cobrado indevidamente",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "role": "assistant",
      "content": "Qual operadora te cobrou?",
      "timestamp": "2024-01-15T10:30:05"
    }
  ],
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/v1/conversations/$CONV_ID
```

---

### 5️⃣ Obter Análise Final

**Endpoint:** `GET /api/v1/conversations/{conversation_id}/analysis`

**Response (antes de finalizar):**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_finalized": false,
  "analysis": null
}
```

**Response (após finalizar):**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_finalized": true,
  "analysis": {
    "problem": "Cobrança indevida de R$ 89,90 por 3 meses pela NET Claro",
    "rights": [
      "CDC Art. 42 - Repetição de indébito em dobro",
      "CDC Art. 6º - Direito à reparação de danos"
    ],
    "estimatedValue": 539.40,
    "recommendations": [
      {
        "type": "amigavel",
        "score": 7.5,
        "reason": "Empresa geralmente aceita acordo direto"
      },
      {
        "type": "extrajudicial",
        "score": 8.0,
        "reason": "Procon tem histórico de sucesso"
      },
      {
        "type": "judicial",
        "score": 6.0,
        "reason": "Valor pode ser resolvido em JEC"
      }
    ],
    "userInfo": {
      "name": "João Silva",
      "cpf": "123.456.789-00",
      "email": "joao@example.com",
      "phone": "(11) 98765-4321",
      "address": "Rua Exemplo, 123"
    },
    "opposingParty": {
      "type": "pj",
      "name": "NET Claro",
      "document": "12.345.678/0001-00",
      "email": "sac@claro.com.br",
      "phone": "0800-123-4567",
      "address": "Av. Paulista, 1000"
    },
    "caseDetails": {
      "title": "Cobrança indevida - NET Claro",
      "description": "Cliente cobrado R$ 89,90 por 3 meses após cancelamento",
      "expectedSolution": "Restituição em dobro + cancelamento definitivo",
      "documents": ["comprovante_pagamento.pdf", "protocolo_cancelamento.pdf"]
    }
  }
}
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/v1/conversations/$CONV_ID/analysis
```

---

## 🔄 Fluxo Completo de Uso

### Exemplo Python Completo

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Iniciar conversa
response = requests.post(f"{BASE_URL}/conversations", json={"tone": "conciliador"})
conv_data = response.json()
conv_id = conv_data["conversation_id"]
print(f"✅ Conversa iniciada: {conv_id}")

# 2. Enviar mensagens
messages = [
    "Fui cobrado indevidamente pela operadora",
    "Foi a NET Claro",
    "R$ 89,90 por 3 meses seguidos",
    "Sim, tentei ligar mas não resolveram",
    "João Silva, CPF 123.456.789-00",
    "joao@example.com, (11) 98765-4321",
    "Pronto, já falei tudo. Pode analisar meu caso"
]

for msg in messages:
    response = requests.post(
        f"{BASE_URL}/conversations/{conv_id}/messages",
        json={"message": msg, "stream": False}
    )
    data = response.json()
    print(f"\n👤 Você: {msg}")
    print(f"🤖 Zellu: {data['message']}")

    if data['is_finalized']:
        print("\n✅ Conversa finalizada!")
        break

# 3. Obter análise final
response = requests.get(f"{BASE_URL}/conversations/{conv_id}/analysis")
analysis_data = response.json()

if analysis_data['is_finalized']:
    analysis = analysis_data['analysis']
    print("\n📊 ANÁLISE DO CASO:")
    print(f"Problema: {analysis['problem']}")
    print(f"Valor estimado: R$ {analysis['estimatedValue']:.2f}")
    print(f"Direitos: {', '.join(analysis['rights'])}")
    print("\nRecomendações:")
    for rec in analysis['recommendations']:
        print(f"  - {rec['type']}: {rec['score']}/10 - {rec['reason']}")
```

---

## 🎯 Finalização Automática

A conversa é automaticamente finalizada quando:

1. **Usuário solicita explicitamente:**
   - Palavras-chave: "finalizar", "terminar", "é isso", "só isso", "pronto", "pode analisar"

2. **Heurística de mensagens:**
   - Após 7+ mensagens do usuário
   - IA detecta que tem informações suficientes

**Quando finalizada:**
- `is_finalized: true`
- `analysis` disponível em `/analysis` endpoint
- Não aceita mais mensagens (retorna erro 400)

---

## 🔧 Configurações

### Variáveis de Ambiente (.env)

```env
# API Keys (obrigatório)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Aplicação
APP_NAME=Zellu
APP_VERSION=1.0.0
ENV=development

# Segurança
X_API_KEY=your-secret-key

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Tom de Voz Adaptativo

```python
# Conciliador (padrão)
{
  "tone": "conciliador"
  # Linguagem acessível, calorosa, empática
  # Exemplo: "Entendo sua frustração 😔 Vamos resolver isso juntos!"
}

# Formal
{
  "tone": "formal"
  # Profissional, respeitoso, eficiente
  # Exemplo: "Compreendo a situação. Para prosseguir, preciso de..."
}

# Técnico
{
  "tone": "tecnico"
  # Terminologia jurídica, referências legais
  # Exemplo: "Conforme CDC Art. 42, você tem direito a..."
}
```

---

## 📊 Estrutura de AnalysisData

```typescript
interface AnalysisData {
  problem: string;                    // Descrição do problema (1-2 frases)
  rights: string[];                   // Direitos aplicáveis com base legal
  estimatedValue: number;             // Valor estimado (> 0)
  recommendations: Recommendation[];  // EXATAMENTE 3 recomendações
  userInfo: UserInfo;
  opposingParty: OpposingParty;
  caseDetails: CaseDetails;
}

interface Recommendation {
  type: "amigavel" | "extrajudicial" | "judicial";
  score: number;  // 0-10
  reason: string;
}
```

---

## 🐛 Tratamento de Erros

**404 - Conversa não encontrada:**
```json
{
  "detail": "Conversa xyz não encontrada"
}
```

**400 - Conversa já finalizada:**
```json
{
  "detail": "Conversa já foi finalizada"
}
```

**500 - Erro do servidor:**
```json
{
  "detail": "Internal server error"
}
```

---

## 🧪 Testando com cURL

```bash
# 1. Iniciar conversa
CONV_ID=$(curl -s -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"tone":"conciliador"}' | jq -r '.conversation_id')

echo "Conversation ID: $CONV_ID"

# 2. Enviar mensagem
curl -X POST http://localhost:8000/api/v1/conversations/$CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"Fui cobrado indevidamente","stream":false}' | jq

# 3. Ver histórico
curl http://localhost:8000/api/v1/conversations/$CONV_ID | jq

# 4. Ver análise
curl http://localhost:8000/api/v1/conversations/$CONV_ID/analysis | jq
```

---

## 📚 Links Úteis

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Debug Routes:** http://localhost:8000/_debug/routes

---

## 🎉 Pronto!

Agora você pode integrar a Zellu AI em qualquer aplicação usando esta API REST! 🚀
