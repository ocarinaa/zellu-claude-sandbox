# 📚 Documentação Técnica Zellu IA

Esta pasta contém toda a documentação técnica do projeto Zellu IA.

## 📑 Índice de Documentos

### 1. Visão Geral
- **[business-requirements.md](./business-requirements.md)** - Problema de negócio e objetivos
- **[product-vision.md](./product-vision.md)** - Visão completa do produto final
- **[current-status.md](./current-status.md)** - O que está implementado vs planejado

### 2. Funcionalidades
- **[solutions-workflow.md](./solutions-workflow.md)** - Detalhamento das 3 soluções (Amigável, Extrajudicial, Judicial)
- **[ticket-system.md](./ticket-system.md)** - Sistema de chamados e estados
- **[escalation-rules.md](./escalation-rules.md)** - Regras de escalação entre soluções

### 3. Personas
- **[persona-cliente.md](./persona-cliente.md)** - Módulo Cliente completo
- **[persona-empresa.md](./persona-empresa.md)** - Módulo Empresa completo
- **[persona-advogado.md](./persona-advogado.md)** - Módulo Advogado completo

### 4. Arquitetura Técnica
- **[technical-stack.md](./technical-stack.md)** - Stack tecnológica e integrações
- **[database-schema.md](./database-schema.md)** - Modelagem de dados
- **[integrations.md](./integrations.md)** - APIs e serviços externos

### 5. Planejamento
- **[roadmap.md](./roadmap.md)** - Cronograma de 6 meses
- **[implementation-phases.md](./implementation-phases.md)** - Fases de desenvolvimento
- **[metrics.md](./metrics.md)** - KPIs e métricas de sucesso

---

## 🎯 Status Atual do Projeto

**Última atualização:** Janeiro 2025

### ✅ Implementado (FASE 1-4E)
- Chat conversacional com IA streaming (SSE)
- Análise de casos do consumidor
- Geração de recomendações ranqueadas
- Cálculo de valores estimados
- RAG com CDC (60 artigos em 11 categorias)
- Persistência de conversas (PostgreSQL + Redis)
- Upload de documentos com validação
- Sistema de heurísticas (ValueEstimator, RecommendationScorer)
- LangGraph state machine (5 nodes)
- 18 testes unitários, 11 integração, 5 e2e

### 🔄 Em Desenvolvimento
- Sistema de tickets/chamados com workflow
- Escalação automática entre soluções
- Sistema de notificações e prazos

### 📋 Planejado (FASE 5+)
- Portal Empresa completo
- Portal Advogado e marketplace
- Sistema de reputação
- Integrações externas (Autentique, JUDIT, WhatsApp)
- Sistema de monetização

---

## 🚀 Como Usar Esta Documentação

1. **Para novos desenvolvedores:** Comece por `business-requirements.md` e `product-vision.md`
2. **Para implementar features:** Consulte os docs de persona específica e `solutions-workflow.md`
3. **Para entender o código atual:** Leia `current-status.md` e `implementation-phases.md`
4. **Para planejar próximos passos:** Veja `roadmap.md` e compare com `current-status.md`

---

## 📝 Contribuindo com a Documentação

Esta documentação deve ser atualizada sempre que:
- Uma nova fase for implementada
- Features forem adicionadas ou modificadas
- Decisões arquiteturais forem tomadas
- Integrações forem adicionadas

**Mantenha a documentação sincronizada com o código!**
