# API de Upload para Serviço IA

**Versão:** 1.0
**Data:** 17/10/2025
**Público-alvo:** Equipe do Serviço IA
**Status:** ✅ Produção Ready

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Autenticação](#autenticação)
3. [Endpoint](#endpoint)
4. [Request Format](#request-format)
5. [Response Format](#response-format)
6. [Validações e Limites](#validações-e-limites)
7. [Exemplos Práticos](#exemplos-práticos)
8. [Tratamento de Erros](#tratamento-de-erros)
9. [Rate Limiting](#rate-limiting)
10. [FAQ](#faq)

---

## 📖 Visão Geral

A API de Upload permite que o serviço IA faça upload de arquivos e áudios gerados durante o processamento, obtendo URLs públicas para incluir nas mensagens enviadas ao sistema Zellu.

### **Propósito**

Quando o serviço IA gera arquivos (relatórios PDF, áudios sintetizados, etc.), ele precisa:

1. Fazer upload do arquivo via esta API
2. Receber a URL pública do arquivo
3. Incluir a URL no webhook `/api/chat/webhook`

### **URL do Endpoint**

```
Produção:  POST https://zellu-app.com/api/ai-service/upload
Staging:   POST https://staging.zellu-app.com/api/ai-service/upload
Dev Local: POST http://localhost:8655/api/ai-service/upload
```

---

## 🔐 Autenticação

### **Método: API Key via Header**

Todas as requisições devem incluir o header `x-api-key`:

```http
x-api-key: {API_KEY_ZELLU_IA}
```

### **Como Obter a Chave**

A chave `API_KEY_ZELLU_IA` é a mesma utilizada no webhook de resposta. Ela já está configurada no serviço IA.

**Exemplo de valor (não usar em produção):**
```
x-api-key: super-api-key-secret-ai-service
```

### **Segurança**

- ✅ Nunca exponha a API key em logs ou código versionado
- ✅ Use variáveis de ambiente
- ✅ Rotacione a chave periodicamente (recomendado: trimestral)

---

## 🌐 Endpoint

### **POST /api/ai-service/upload**

**Headers Obrigatórios:**
```http
Content-Type: multipart/form-data
x-api-key: {API_KEY_ZELLU_IA}
```

**Body (FormData):**
```
files: File[]  // Array de 1 ou mais arquivos
```

**Características:**
- ✅ Aceita upload único ou múltiplo
- ✅ Processa em ordem sequencial
- ✅ Retorna URLs públicas do MinIO
- ✅ Rate limiting: 10 requisições/minuto

---

## 📤 Request Format

### **Estrutura do FormData**

```javascript
const formData = new FormData();
formData.append('files', file1);  // Primeiro arquivo
formData.append('files', file2);  // Segundo arquivo (opcional)
formData.append('files', file3);  // Terceiro arquivo (opcional)
```

### **Exemplo de Requisição (fetch)**

```javascript
const formData = new FormData();
formData.append('files', pdfBlob, 'relatorio.pdf');
formData.append('files', audioBlob, 'resposta.mp3');

const response = await fetch('https://zellu-app.com/api/ai-service/upload', {
  method: 'POST',
  headers: {
    'x-api-key': process.env.API_KEY_ZELLU_IA,
  },
  body: formData,
});

const data = await response.json();
console.log('URLs dos arquivos:', data.files);
```

### **Exemplo de Requisição (curl)**

```bash
curl -X POST https://zellu-app.com/api/ai-service/upload \
  -H "x-api-key: super-api-key-secret-ai-service" \
  -F "files=@/path/to/relatorio.pdf" \
  -F "files=@/path/to/audio.mp3"
```

---

## 📥 Response Format

### **Sucesso Total (200 OK)**

Todos os arquivos foram enviados com sucesso.

```json
{
  "success": true,
  "files": [
    {
      "url": "https://minio-s3.147.93.9.113.sslip.io/zellu-minio-data/chat-ticket-files/ai-uploads/1729012345678-relatorio.pdf",
      "mimeType": "application/pdf",
      "filename": "relatorio.pdf",
      "size": 245760
    },
    {
      "url": "https://minio-s3.147.93.9.113.sslip.io/zellu-minio-data/chat-ticket-files/ai-uploads/1729012345679-audio.mp3",
      "mimeType": "audio/mpeg",
      "filename": "audio.mp3",
      "size": 524288
    }
  ]
}
```

### **Sucesso Parcial (200 OK)**

Alguns arquivos falharam, mas pelo menos 1 foi enviado.

```json
{
  "success": true,
  "uploadStatus": "partial",
  "files": [
    {
      "url": "https://minio-s3.../relatorio.pdf",
      "mimeType": "application/pdf",
      "filename": "relatorio.pdf",
      "size": 245760
    }
  ],
  "warnings": [
    "arquivo-grande.bin: Arquivo excede 50MB (tamanho: 75.23MB)",
    "malware.exe: Tipo de arquivo não permitido (.exe - application/x-msdownload)"
  ]
}
```

### **Erro Completo (400 Bad Request)**

Todos os arquivos falharam.

```json
{
  "error": "Nenhum arquivo pôde ser enviado",
  "details": [
    "arquivo1.exe: Tipo de arquivo não permitido",
    "arquivo2.bin: Arquivo excede 50MB"
  ]
}
```

### **Rate Limit Excedido (429 Too Many Requests)**

```json
{
  "error": "Taxa de requisições excedida. Aguarde 42 segundos.",
  "retryAfter": 42
}
```

**Headers da resposta:**
```http
Retry-After: 42
```

### **Não Autorizado (401 Unauthorized)**

```json
{
  "error": "Não autorizado"
}
```

### **Erro no Servidor (500 Internal Server Error)**

```json
{
  "error": "Erro ao processar upload"
}
```

---

## 🛡️ Validações e Limites

### **Tamanhos Máximos**

| Tipo | Limite | Comportamento ao Exceder |
|------|--------|--------------------------|
| **Arquivo individual** | 50 MB | Arquivo rejeitado (outros continuam) |
| **Total da requisição** | 100 MB | Requisição inteira rejeitada (400) |

### **MIME Types Permitidos**

#### **Áudio**
- `audio/webm`
- `audio/mpeg` (MP3)
- `audio/wav`
- `audio/ogg`
- `audio/m4a`

#### **Vídeo**
- `video/mp4`
- `video/webm`
- `video/avi`
- `video/quicktime` (MOV)

#### **Imagem**
- `image/jpeg`, `image/jpg`
- `image/png`
- `image/gif`
- `image/webp`
- `image/svg+xml`

#### **Documentos**
- `application/pdf`
- `application/msword` (DOC)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- `application/vnd.ms-excel` (XLS)
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX)
- `text/csv`

#### **Arquivos Compactados**
- `application/zip`
- `application/x-rar-compressed`
- `application/x-7z-compressed`

#### **Outros**
- `application/json`
- `text/plain`

### **Validação de Filename**

Os nomes de arquivo são **sanitizados automaticamente**:

| Original | Sanitizado |
|----------|------------|
| `Relatório Final - IA.pdf` | `1729012345678-relatorio-final-ia.pdf` |
| `Áudio Resposta (v2).mp3` | `1729012345679-audio-resposta-v2.mp3` |
| `Contrato PJ - M.A.M.pdf` | `1729012345680-contrato-pj-m-a-m.pdf` |

**Regras de sanitização:**
1. Adiciona timestamp para unicidade
2. Remove acentos
3. Converte para minúsculas
4. Substitui caracteres especiais por hífen
5. Limita a 100 caracteres

---

## 💻 Exemplos Práticos

### **Exemplo 1: Upload Único (JavaScript/Node.js)**

```javascript
import fs from 'fs';
import FormData from 'form-data';
import fetch from 'node-fetch';

async function uploadFile() {
  const formData = new FormData();
  formData.append('files', fs.createReadStream('./relatorio.pdf'));

  const response = await fetch('https://zellu-app.com/api/ai-service/upload', {
    method: 'POST',
    headers: {
      'x-api-key': process.env.API_KEY_ZELLU_IA,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  const data = await response.json();
  const fileUrl = data.files[0].url;

  console.log('Arquivo enviado:', fileUrl);
  return fileUrl;
}
```

### **Exemplo 2: Upload Múltiplo (JavaScript)**

```javascript
async function uploadMultipleFiles(files) {
  const formData = new FormData();

  files.forEach(file => {
    formData.append('files', file.buffer, file.name);
  });

  const response = await fetch('https://zellu-app.com/api/ai-service/upload', {
    method: 'POST',
    headers: {
      'x-api-key': process.env.API_KEY_ZELLU_IA,
    },
    body: formData,
  });

  const data = await response.json();

  if (data.warnings) {
    console.warn('Alguns arquivos falharam:', data.warnings);
  }

  return data.files.map(f => f.url);
}
```

### **Exemplo 3: Python com Requests**

```python
import requests
import os

def upload_file(file_path):
    url = 'https://zellu-app.com/api/ai-service/upload'
    headers = {
        'x-api-key': os.environ['API_KEY_ZELLU_IA']
    }

    with open(file_path, 'rb') as f:
        files = {'files': f}
        response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()
    data = response.json()

    return data['files'][0]['url']

# Uso
file_url = upload_file('./relatorio.pdf')
print(f'URL do arquivo: {file_url}')
```

### **Exemplo 4: curl (Linha de Comando)**

```bash
# Upload único
curl -X POST https://zellu-app.com/api/ai-service/upload \
  -H "x-api-key: $API_KEY_ZELLU_IA" \
  -F "files=@relatorio.pdf"

# Upload múltiplo
curl -X POST https://zellu-app.com/api/ai-service/upload \
  -H "x-api-key: $API_KEY_ZELLU_IA" \
  -F "files=@relatorio.pdf" \
  -F "files=@audio.mp3" \
  -F "files=@imagem.jpg"
```

---

## 🚨 Tratamento de Erros

### **Tabela de Códigos de Erro**

| Código | Erro | Causa Comum | Solução |
|--------|------|-------------|---------|
| **200** | Sucesso | Upload bem-sucedido | Usar URLs retornadas |
| **400** | Bad Request | Arquivo muito grande ou tipo inválido | Verificar validações |
| **401** | Unauthorized | API key ausente/inválida | Verificar header `x-api-key` |
| **429** | Too Many Requests | Rate limit excedido (>10 req/min) | Aguardar tempo em `retryAfter` |
| **500** | Internal Server Error | Erro no MinIO ou servidor | Fazer retry com backoff |

### **Retry Logic Recomendado**

#### **Estratégia de Retry com Exponential Backoff**

```javascript
async function uploadWithRetry(formData, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch('https://zellu-app.com/api/ai-service/upload', {
        method: 'POST',
        headers: { 'x-api-key': process.env.API_KEY_ZELLU_IA },
        body: formData,
      });

      // Sucesso
      if (response.ok) {
        return await response.json();
      }

      // Rate limit → aguardar tempo específico
      if (response.status === 429) {
        const data = await response.json();
        const retryAfter = data.retryAfter || 60;
        console.log(`Rate limit. Aguardando ${retryAfter}s...`);
        await sleep(retryAfter * 1000);
        continue; // Tenta novamente
      }

      // Erro 4xx (exceto 429) → não tentar novamente
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`Erro de validação: ${response.statusText}`);
      }

      // Erro 5xx → retry com backoff
      if (response.status >= 500) {
        const backoff = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s
        console.log(`Erro 500. Retry em ${backoff}ms...`);
        await sleep(backoff);
        continue;
      }

    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      const backoff = Math.pow(2, attempt) * 1000;
      await sleep(backoff);
    }
  }

  throw new Error('Max retries atingido');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### **Tratamento de Erros Parciais**

```javascript
const result = await uploadFiles(formData);

if (result.uploadStatus === 'partial') {
  console.warn('⚠️ Alguns arquivos falharam:');
  result.warnings.forEach(warning => console.warn(`  - ${warning}`));

  console.log('✅ Arquivos enviados com sucesso:');
  result.files.forEach(file => console.log(`  - ${file.filename}: ${file.url}`));
}
```

---

## ⏱️ Rate Limiting

### **Limites Atuais**

| Métrica | Limite |
|---------|--------|
| **Requisições por minuto** | 10 |
| **Janela de tempo** | 60 segundos (deslizante) |
| **Identificador** | IP de origem |

### **Como Funciona (Sliding Window)**

```
Exemplo: Limite de 10 req/min

Tempo:  00:00  00:15  00:30  00:45  01:00  01:15
Req:      5      3      2      1      ✅     ❌

✅ 01:00 - OK (janela: 00:00-01:00 = 11 requisições, mas req de 00:00 já expiraram)
❌ 01:15 - BLOQUEADO (janela: 00:15-01:15 = 10 requisições ativas)
```

### **Header de Resposta**

Quando o rate limit é excedido, a resposta inclui:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42

{
  "error": "Taxa de requisições excedida. Aguarde 42 segundos.",
  "retryAfter": 42
}
```

### **Como Evitar Rate Limit**

1. ✅ **Batch de arquivos:** Envie múltiplos arquivos em uma única requisição
2. ✅ **Cache local:** Evite re-upload do mesmo arquivo
3. ✅ **Implementar retry:** Respeite o `retryAfter` quando receber 429
4. ❌ **Não faça:** Polling agressivo ou loops sem delay

---

## ❓ FAQ

### **1. Posso enviar múltiplos arquivos em uma requisição?**

**R:** Sim! Use o mesmo campo `files` múltiplas vezes:

```javascript
formData.append('files', file1);
formData.append('files', file2);
formData.append('files', file3);
```

**Limite:** 100MB total (soma de todos os arquivos).

---

### **2. Como saber se atingi o rate limit?**

**R:** A resposta retorna status `429` com o campo `retryAfter`:

```json
{
  "error": "Taxa de requisições excedida. Aguarde 42 segundos.",
  "retryAfter": 42
}
```

Aguarde `retryAfter` segundos antes de tentar novamente.

---

### **3. O que acontece se um arquivo falhar no meio do upload?**

**R:** Processamento continua para os outros arquivos (graceful degradation):

- ✅ Arquivos válidos → enviados com sucesso
- ❌ Arquivos inválidos → listados em `warnings`
- ✅ Response status: `200 OK` com `uploadStatus: "partial"`

---

### **4. As URLs dos arquivos expiram?**

**R:** Não. As URLs são públicas e permanentes enquanto o arquivo existir no MinIO.

**Formato da URL:**
```
https://minio-s3.147.93.9.113.sslip.io/zellu-minio-data/chat-ticket-files/ai-uploads/{timestamp}-{filename}
```

---

### **5. Como usar a URL no webhook?**

**R:** Após fazer upload, inclua a URL no webhook:

```javascript
// 1. Upload do arquivo
const uploadResponse = await fetch('https://zellu-app.com/api/ai-service/upload', {
  method: 'POST',
  headers: { 'x-api-key': API_KEY },
  body: formData,
});
const { files } = await uploadResponse.json();
const fileUrl = files[0].url;

// 2. Enviar no webhook
await fetch('https://zellu-app.com/api/chat/webhook', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': API_KEY,
  },
  body: JSON.stringify({
    chat_id: '...',
    message: 'Análise completa! Veja o relatório anexo.',
    files: [fileUrl],  // ← URL do upload
    is_finished: true,
  }),
});
```

---

### **6. Quais tipos de arquivo NÃO são permitidos?**

**R:** Tipos executáveis e potencialmente perigosos:

- ❌ `.exe`, `.bat`, `.cmd`, `.sh`
- ❌ `.dll`, `.so`
- ❌ `.app`, `.dmg`
- ❌ Arquivos sem extensão reconhecida

**Validação:** Baseada no MIME type, não apenas na extensão.

---

### **7. Como testar localmente?**

**R:** Use `localhost:8655`:

```bash
curl -X POST http://localhost:8655/api/ai-service/upload \
  -H "x-api-key: super-api-key-secret-ai-service" \
  -F "files=@test.pdf"
```

Verifique o `.env` local para confirmar `API_KEY_ZELLU_IA`.

---

### **8. O que fazer se receber erro 500?**

**R:** Erro no servidor (MinIO ou backend). Ações recomendadas:

1. ✅ Fazer retry com exponential backoff (3 tentativas)
2. ✅ Verificar logs do servidor (se tiver acesso)
3. ✅ Reportar ao time de backend se persistir

**Não recomendado:** Retry infinito sem backoff.

---

## 📚 Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `docs/AI_SERVICE_UPLOAD_API.md` | Este documento (documentação da API de upload) |
| `docs/AI_SERVICE_WEBHOOK_FORMAT.md` | Documentação do webhook (request/response) |
| `docs/MELHORIAS_FUTURAS_SEGURANCA.md` | Melhorias de segurança planejadas |
| `src/app/api/ai-service/upload/route.ts` | Implementação do endpoint |
| `src/lib/rate-limit.ts` | Implementação do rate limiter |
| `src/lib/storage.ts` | Lógica de upload para MinIO/S3 |

---

## 🎯 Checklist de Integração

### **Para o Serviço IA:**

- [ ] Obter `API_KEY_ZELLU_IA` do time de backend
- [ ] Configurar variável de ambiente no serviço IA
- [ ] Testar upload em ambiente de staging
- [ ] Implementar retry logic com exponential backoff
- [ ] Implementar tratamento de rate limit (429)
- [ ] Validar URLs retornadas antes de enviar no webhook
- [ ] Testar upload de arquivos grandes (~40MB)
- [ ] Testar upload de múltiplos arquivos
- [ ] Configurar logs de upload (sucesso/falha)
- [ ] Validar fluxo completo: upload → webhook → frontend

---

**Documentação atualizada em:** 17/10/2025
**Versão:** 1.0
**Autor:** Time Zellu Backend

**Para dúvidas ou suporte:** Entre em contato com o time de backend.

---

✅ **API pronta para uso em produção!** 🚀
