# Webhook Integration - Zellu IA

Este documento explica como usar a integração webhook entre o serviço de IA e o aplicativo Zellu.

## Visão Geral

A integração webhook permite que o frontend/backend do Zellu se comunique com o serviço de IA de forma assíncrona:

```
Frontend Zellu → Backend Zellu → Webhook → Python IA Service
                                           ↓
                                     LangGraph Processing
                                           ↓
                                     Callback → Backend Zellu → Frontend
```

### Capacidades da IA

A IA processa conversas com as seguintes tecnologias:

- **LangGraph:** 5 nodes (collector, validator, decider, analyzer, finisher)
- **RAG:** 90 artigos do CDC (Código de Defesa do Consumidor)
- **Jurisprudência:** Valores baseados em decisões reais do STJ e TJs (2020-2024)
- **Heurísticas:** Cálculo automático de valores e recomendações inteligentes
- **OCR:** Processamento de documentos (PDFs e imagens)
- **Checkpoints:** Memória de contexto com Redis
- **Sistema de Tickets:** Criação automática quando conversa finaliza

## Arquivos Criados/Modificados

### 1. **src/api/routes/webhook.py** (NOVO)
Endpoint principal do webhook que:
- Recebe mensagens do usuário via POST /webhook/chat
- Recupera estado da conversa (checkpoints)
- Processa com LangGraph (collector_node, finisher_node)
- Gera análise jurídica quando confiança >= 80%
- Envia callback assíncrono ao Zellu

### 2. **src/zellu/app.py** (MODIFICADO)
- Adicionado import do webhook router
- Registrado router: `app.include_router(webhook.router)`

### 3. **.env** (MODIFICADO)
- Adicionado: `ZELLU_WEBHOOK_URL` (URL de callback)
- Adicionado: `API_KEY_ZELLU_IA` (chave de autenticação)

### 4. **test_webhook_integration.py** (NOVO)
Script de teste para validar a integração

## Configuração

### Passo 1: Variáveis de Ambiente

Edite o arquivo `.env` e configure:

```bash
# Webhook Integration (Zellu App)
ZELLU_WEBHOOK_URL=http://zellu-ia.147.93.9.113.sslip.io/api/chat/webhook
API_KEY_ZELLU_IA=sua-chave-api-aqui
```

**IMPORTANTE**: Solicite ao time de backend:
- A URL correta do callback (pode ser diferente)
- A chave API válida para autenticação

### Passo 2: Iniciar Dependências

Certifique-se que Redis e PostgreSQL estão rodando:

```bash
docker-compose up -d
```

### Passo 3: Iniciar o Servidor

```bash
uvicorn src.zellu.app:app --reload --host 0.0.0.0 --port 8000
```

## Testando a Integração

### Teste Local (Mock)

Execute o script de teste:

```bash
python test_webhook_integration.py
```

Opções disponíveis:
1. **Simple Ping**: Testa se o endpoint responde
2. **Conversa Completa**: Simula 3 mensagens até gerar análise
3. **Ambos**: Executa os dois testes

### Teste com Frontend Real

1. **Configure o webhook no backend do Zellu**:
   - Endpoint: `http://SEU_IP:8000/webhook/chat`
   - Method: POST
   - Headers: `Content-Type: application/json`

2. **Faça login no frontend**:
   - URL: http://zellu-ia.147.93.9.113.sslip.io
   - Email: gabrielmlopes8@gmail.com
   - Senha: Ddj34mkwwh@1

3. **Inicie uma conversa**:
   - Digite uma mensagem sobre um problema jurídico
   - Aguarde resposta da IA
   - Continue a conversa até gerar análise completa

## Formato da API

### REQUEST (Zellu → IA)

**POST /webhook/chat**

```json
{
  "id": "uuid-da-mensagem",
  "chat_id": "uuid-da-sessao",
  "nome": "João Silva",
  "message_type": "text",
  "body_message": "Fui cobrado indevidamente...",
  "audio": null,
  "files": []
}
```

### RESPONSE (IA → Zellu via Callback)

**POST {ZELLU_WEBHOOK_URL}**

Headers:
```
Content-Type: application/json
x-api-key: {API_KEY_ZELLU_IA}
```

Body:
```json
{
  "chat_id": "uuid-da-sessao",
  "message": "Resposta da IA...",
  "is_finished": false,
  "message_type": "text",
  "files": [],
  "audio": null,
  "analysis_data": null
}
```

### RESPONSE Final (com análise)

Quando `is_finished: true`:

```json
{
  "chat_id": "uuid-da-sessao",
  "message": "Análise concluída! Aqui está o resumo...",
  "is_finished": true,
  "message_type": "text",
  "analysis_data": {
    "problem": "Cobrança indevida de R$ 89,90...",
    "rights": [
      "CDC Art. 42 - Direito à devolução em dobro",
      "CDC Art. 6 - Direitos básicos violados"
    ],
    "estimatedValue": 1500.00,
    "recommendations": [
      {
        "type": "amigavel",
        "score": 7.5,
        "reason": "Baixo valor e boa documentação"
      },
      {
        "type": "extrajudicial",
        "score": 8.0,
        "reason": "Procon pode resolver rapidamente"
      },
      {
        "type": "judicial",
        "score": 4.0,
        "reason": "Custo-benefício desfavorável"
      }
    ],
    "userInfo": {
      "name": "João Silva Santos",
      "cpf": "123.456.789-00",
      "email": "joao@email.com",
      "phone": "(11) 98765-4321"
    },
    "opposingParty": {
      "type": "pj",
      "name": "TelecomX"
    },
    "caseDetails": {
      "title": "Cobrança Indevida - TelecomX",
      "description": "Cliente cobrado por serviço cancelado..."
    }
  }
}
```

## Fluxo de Processamento

### 1. Recepção da Mensagem
- Webhook recebe POST /webhook/chat
- Valida payload com Pydantic (WebhookRequest)

### 2. Recuperação de Estado
- Busca checkpoint no Redis pelo chat_id
- Se não existe: cria novo estado
- Se existe: recupera conversa anterior

### 3. Processamento LangGraph
- Adiciona mensagem do usuário ao histórico
- Executa `collector_node` para extrair informações
- Incrementa turn_count

### 4. Decisão de Finalização
- Verifica confiança (confidence_score >= 0.8)
- Verifica número de turnos (turn_count >= 3)
- Se ambos verdadeiros → finaliza

### 5. Análise Final (se finalizar)
- Busca artigos CDC relevantes (RAG com 90 artigos)
- Aplica jurisprudência consolidada (STJ/TJs 2020-2024)
- Calcula valores baseados em casos reais
- Executa `finisher_node`
- Gera analysis_data completo

### 6. Checkpoint
- Salva estado atualizado no Redis
- TTL: 24 horas

### 7. Callback Assíncrono
- Envia resposta ao Zellu em background
- Não bloqueia processamento

### 8. Resposta Síncrona
- Retorna status de sucesso ao Zellu
- Não inclui a resposta da IA (virá via callback)

## Logs e Monitoramento

Os logs incluem:

```
[WEBHOOK] Recebida mensagem do chat_id: abc-123
[WEBHOOK] Tipo: text, Usuário: João Silva
[WEBHOOK] Processando com LangGraph...
[WEBHOOK] Confiança: 95%, Finalizar: True
[WEBHOOK] Gerando análise final...
[WEBHOOK] ✅ Análise completa gerada!
[WEBHOOK] Checkpoint salvo: abc-123
[WEBHOOK] Enviando callback ao Zellu: http://...
[WEBHOOK] ✅ Callback enviado com sucesso
```

## Solução de Problemas

### Erro: "❌ API_KEY_ZELLU_IA não configurada!"
- Configure a variável no .env
- Solicite a chave ao time de backend

### Erro: "Callback falhou: 401"
- Verifique se a API key está correta
- Confirme com backend se a chave está ativa

### Erro: "Callback falhou: 404"
- Verifique se ZELLU_WEBHOOK_URL está correto
- Confirme com backend a URL de callback

### Erro: "Redis connection refused"
- Inicie o Redis: `docker-compose up -d`
- Verifique REDIS_URL no .env

### Erro: "PostgreSQL connection refused"
- Inicie o PostgreSQL: `docker-compose up -d`
- Verifique DATABASE_URL no .env

## Próximos Passos

1. **Obter credenciais do backend**:
   - ZELLU_WEBHOOK_URL correto
   - API_KEY_ZELLU_IA válido

2. **Testar com frontend real**:
   - Fazer login no site
   - Iniciar conversa
   - Verificar análise gerada

3. **Implementar features adicionais** (opcional):
   - Suporte a áudio (message_type: "audio")
   - Suporte a arquivos (message_type: "file")
   - Group messages com delays
   - Upload de arquivos gerados pela IA

4. **Deploy em produção**:
   - Configurar servidor público
   - Configurar HTTPS
   - Configurar rate limiting
   - Configurar monitoramento

## Referências

- **AI_SERVICE_WEBHOOK_FORMAT.md**: Especificação completa do webhook
- **AI_SERVICE_UPLOAD_API.md**: API de upload de arquivos
- **ai-service-webhook-example.json**: Exemplo de workflow N8n
- **src/api/routes/webhook.py**: Implementação do endpoint
- **test_webhook_integration.py**: Script de teste

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do servidor
2. Execute o script de teste
3. Consulte a documentação de referência
4. Entre em contato com o time de backend para credenciais
