# GUIA RÁPIDO: Testando o Webhook

## Resumo

A integração webhook foi implementada com sucesso! Agora você pode conectar a IA do Zellu com o frontend.

## O que foi implementado:

✅ Endpoint webhook: **POST /webhook/chat**
✅ Integração com LangGraph existente
✅ Sistema de checkpoint para recuperar conversas
✅ Callback assíncrono ao Zellu
✅ Formato completo de analysis_data
✅ Script de teste incluído
✅ Documentação completa

## PASSO A PASSO PARA TESTAR

### 1. Configurar credenciais (IMPORTANTE!)

Edite o arquivo `.env` e peça ao time de backend as credenciais:

```bash
# Webhook Integration (Zellu App)
ZELLU_WEBHOOK_URL=http://zellu-ia.147.93.9.113.sslip.io/api/chat/webhook
API_KEY_ZELLU_IA=PEDIR_AO_BACKEND
```

**Atenção**: A linha `API_KEY_ZELLU_IA` precisa ser preenchida com a chave real!

### 2. Iniciar dependências

Abra um terminal e execute:

```bash
docker-compose up -d
```

Aguarde Redis e PostgreSQL iniciarem (cerca de 10 segundos).

### 3. Iniciar o servidor da IA

```bash
uvicorn src.zellu.app:app --reload --host 0.0.0.0 --port 8000
```

Você verá:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Zellu IA Service PRONTO!
```

### 4. Testar localmente (OPCIONAL)

Em outro terminal, execute:

```bash
python test_webhook_integration.py
```

Escolha opção **2** (Conversa Completa) para simular 3 mensagens.

### 5. Testar com frontend real

1. **Configure o webhook no backend do Zellu**:
   - Fale com o time de backend para apontar o webhook para:
   - URL: `http://SEU_IP:8000/webhook/chat`
   - Método: POST
   - Headers: Content-Type: application/json

2. **Acesse o site do Zellu**:
   - URL: http://zellu-ia.147.93.9.113.sslip.io
   - Email: gabrielmlopes8@gmail.com
   - Senha: Ddj34mkwwh@1

3. **Inicie uma conversa**:
   - Descreva um problema jurídico
   - Responda as perguntas da IA
   - Após 3-4 mensagens, a análise será gerada

## Exemplo de Conversa

**Usuário**: "Fui cobrado indevidamente pela TelecomX no valor de R$ 89,90"

**IA**: "Entendo sua situação. Você tem documentos da cobrança?"

**Usuário**: "Sim, tenho o extrato e o comprovante de cancelamento"

**IA**: "Ótimo! Para prosseguir, preciso de: nome completo, CPF, email e telefone"

**Usuário**: "João Silva, CPF 123.456.789-00, email joao@email.com, tel (11) 98765-4321"

**IA**: *(Gera análise completa com 3 recomendações)*

## Verificando se está funcionando

### Logs do servidor

Você verá logs como:

```
[WEBHOOK] Recebida mensagem do chat_id: abc-123
[WEBHOOK] Processando com LangGraph...
[WEBHOOK] Confiança: 95%, Finalizar: True
[WEBHOOK] Gerando análise final...
[WEBHOOK] Checkpoint salvo: abc-123
[WEBHOOK] Enviando callback ao Zellu
```

### No frontend

- As mensagens aparecem em tempo real
- Após a 3ª-4ª mensagem, o frontend mostra a análise completa
- Você vê: problema, direitos aplicáveis, valor estimado, 3 recomendações

## Problemas Comuns

### "Redis connection refused"
```bash
docker-compose up -d
```

### "PostgreSQL connection refused"
```bash
docker-compose up -d
```

### "API_KEY_ZELLU_IA não configurada"
- Edite `.env`
- Peça a chave ao time de backend

### "Callback failed: 404"
- Confirme ZELLU_WEBHOOK_URL com backend
- Pode ser que a URL esteja diferente

## Próximos Passos

1. ✅ **Teste localmente** com script de teste
2. 📋 **Obtenha credenciais** do time de backend
3. 🌐 **Configure webhook** no backend
4. 🧪 **Teste com frontend** real
5. 🚀 **Deploy em produção** quando aprovado

## Arquivos Importantes

- **WEBHOOK_INTEGRATION.md**: Documentação técnica completa
- **test_webhook_integration.py**: Script de teste
- **src/api/routes/webhook.py**: Código do webhook
- **.env**: Configurações (inclui credenciais sensíveis)

## Dúvidas?

1. Leia **WEBHOOK_INTEGRATION.md** para detalhes técnicos
2. Execute **test_webhook_integration.py** para diagnóstico
3. Verifique logs do servidor
4. Consulte time de backend para credenciais

---

**STATUS**: Webhook implementado e pronto para testes! 🎉
