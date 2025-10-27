# 🔗 Integrações Externas - Zellu IA

**Última atualização:** 27/10/2025

Esta pasta contém documentação e exemplos de integrações com serviços externos.

---

## 📄 Arquivos Disponíveis

### 1. `ai-service-webhook-example.json`
**Tipo:** Exemplo de Workflow (n8n/Node-RED style)

**Descrição:**
Exemplo completo de como um serviço de IA externo (n8n, Zapier, etc.) deve:
1. Receber mensagens do Zellu via webhook
2. Processar com LLM (OpenAI/Anthropic)
3. Formatar resposta no padrão Zellu
4. Enviar de volta via `POST /api/chat/webhook`

**Formato de Resposta:**
```json
{
  "chat_id": "uuid",
  "message": "Resposta da IA",
  "is_finished": false,
  "message_type": "text",
  "files": [],
  "audio": null,

  // Quando is_finished=true:
  "analysis_data": {
    "problem": "Descrição do problema",
    "rights": ["Direitos identificados"],
    "estimatedValue": 3598.50,
    "recommendations": [
      {
        "type": "amigavel",
        "score": 9.2,
        "reason": "Alta chance de resolução"
      }
    ],
    "userInfo": {...},
    "opposingParty": {...},
    "caseDetails": {...}
  }
}
```

**Autenticação:**
```
Header: x-api-key: <API_KEY_ZELLU_IA do .env>
```

**Quando implementar:**
- Fase 6 ou posterior
- Necessário para integração com serviço IA externo
- Permite criar tickets automaticamente após análise

---

### 2. `AI_SERVICE_UPLOAD_API.md`
**Tipo:** Documentação Técnica Completa

**Descrição:**
API para upload de arquivos gerados pelo serviço IA (relatórios, áudios, etc.).

**Endpoint:** `POST /api/ai-service/upload`

**Funcionalidades:**
- ✅ Upload único ou múltiplo
- ✅ Validação de MIME types
- ✅ Rate limiting (10 req/min)
- ✅ Suporte a 50MB por arquivo
- ✅ Retorna URLs públicas

**Arquivos Suportados:**
- **Áudio:** webm, mp3, wav, ogg, m4a
- **Vídeo:** mp4, webm, avi, mov
- **Imagem:** jpg, png, gif, webp, svg
- **Documentos:** pdf, doc, docx, xls, xlsx, csv
- **Compactados:** zip, rar, 7z
- **Outros:** json, txt

**Exemplo de Uso:**
```javascript
const formData = new FormData();
formData.append('files', pdfBlob, 'relatorio.pdf');

const response = await fetch('https://zellu-app.com/api/ai-service/upload', {
  method: 'POST',
  headers: {
    'x-api-key': process.env.API_KEY_ZELLU_IA,
  },
  body: formData,
});

const { files } = await response.json();
const fileUrl = files[0].url;

// Usar URL no webhook de resposta
await sendWebhook({
  chat_id: '...',
  message: 'Análise completa! Veja o relatório anexo.',
  files: [fileUrl],
  is_finished: true,
});
```

**Quando implementar:**
- Opcional na Fase 6
- Necessário se a IA gerar arquivos (PDFs, áudios)
- Requer MinIO ou S3 configurado

---

## 🔐 Chaves de API

### `API_KEY_ZELLU_IA`
**Localização:** `.env` (linha 24)

**Valor atual:**
```
1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798
```

**Uso:**
- Autenticação de webhooks
- Autenticação da API de upload
- Compartilhar com serviço IA externo

**Header:**
```
x-api-key: 1e2aa5442595cd14ae0b9ce3fc11282db68f13178b3638c494071af4f5eef798
```

---

## 🛣️ Roadmap de Implementação

### Fase 6 (Workflow Soluções)
- [ ] Implementar endpoint `/api/chat/webhook`
- [ ] Validar `x-api-key`
- [ ] Processar `group_messages` (mensagens sequenciais)
- [ ] Criar ticket automaticamente quando `is_finished=true`

### Fase 7+ (Upload de Arquivos)
- [ ] Implementar endpoint `/api/ai-service/upload`
- [ ] Configurar MinIO ou S3
- [ ] Implementar rate limiting
- [ ] Validação de MIME types
- [ ] Retornar URLs públicas

---

## 📚 Referências

| Arquivo | Descrição |
|---------|-----------|
| `ai-service-webhook-example.json` | Exemplo completo de workflow |
| `AI_SERVICE_UPLOAD_API.md` | Documentação da API de upload |
| `../FASE-5-COMPLETA.md` | Status e próximos passos |
| `../../.env` | Chaves e configurações |

---

## ⚠️ Notas Importantes

1. **Segurança:**
   - Nunca expor `API_KEY_ZELLU_IA` em código versionado
   - Sempre usar HTTPS em produção
   - Rotacionar chave trimestralmente

2. **Validação:**
   - Sempre validar header `x-api-key`
   - Retornar 401 se inválido
   - Logar tentativas de acesso não autorizado

3. **Rate Limiting:**
   - API de upload: 10 req/min por IP
   - Webhook: sem limite (confiável)
   - Implementar backoff exponencial

---

**Documentação mantida em:** `docs/integrations/`
**Para dúvidas:** Consultar equipe de backend
