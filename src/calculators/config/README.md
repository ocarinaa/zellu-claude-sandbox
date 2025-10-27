# Configuração de Regras de Negócio

Este diretório contém as regras de negócio editáveis para cálculo de valores e recomendações do Zellu IA.

## 📄 Arquivo Principal

**`rules_config.json`** - Contém todas as regras configuráveis:
- Valores base por artigo CDC
- Multiplicadores de dano
- Scores de recomendações
- Limites e thresholds

## 🎯 Como Funciona

O sistema carrega automaticamente as regras do JSON ao iniciar. Se o arquivo não existir ou estiver inválido, usa valores padrão do código (`rules.py`).

## ✏️ Como Editar

### 1. Ajustar Valores de Dano por Artigo CDC

Para modificar quanto um artigo específico vale:

```json
"cdc_value_rules": {
  "42": {
    "description": "Devolução em dobro + dano moral",
    "multiplier": 2.0,           ← Multiplica valor cobrado
    "moral_damage_base": 2000.0, ← Dano moral base (R$)
    "legal_reference": "Art. 42 - Cobrança indevida"
  }
}
```

**Exemplo**: Se quiser aumentar dano moral do Art. 42 de R$ 2.000 para R$ 3.000:
```json
"moral_damage_base": 3000.0
```

### 2. Modificar Limites Gerais

```json
"estimator_settings": {
  "min_value": 500,    ← Valor mínimo de qualquer caso
  "max_value": 50000,  ← Valor máximo (cap)
  "bonus_multipliers": {
    "has_documents": 1.2,          ← +20% se tem docs
    "multiple_violations": 1.3     ← +30% se 3+ violações
  }
}
```

**Exemplo**: Para aumentar bonus de documentação para 30%:
```json
"has_documents": 1.3
```

### 3. Ajustar Scores de Recomendações

```json
"recommendation_base_scores": {
  "amigavel": {
    "base": 7.0,  ← Score inicial
    "max": 10.0   ← Score máximo possível
  }
}
```

**Exemplo**: Para tornar resolução amigável menos favorável por padrão:
```json
"base": 6.0
```

### 4. Modificar Condições que Afetam Scores

```json
"score_modifiers": {
  "has_documents": {
    "amigavel": 1.0,       ← +1.0 no score amigável
    "extrajudicial": 0.5,  ← +0.5 no extrajudicial
    "judicial": 0.3        ← +0.3 no judicial
  },
  "low_value": {
    "threshold": 1000,     ← Define o que é "valor baixo"
    "amigavel": 1.0,
    "judicial": -0.5       ← Reduz score judicial
  }
}
```

## 🔄 Aplicar Mudanças

### Em Desenvolvimento
1. Edite o `rules_config.json`
2. Salve o arquivo
3. Reinicie o servidor FastAPI
4. As novas regras entram em vigor imediatamente

### Em Produção
```bash
# Opção 1: Reiniciar aplicação
docker-compose restart zellu-api

# Opção 2: Hot-reload (se implementado)
curl -X POST http://localhost:8000/api/admin/reload-config
```

## ✅ Validar Configuração

Após editar, valide se o JSON está correto:

```bash
# Validar JSON syntax
python -m json.tool rules_config.json

# Validar regras (via teste)
pytest tests/unit/test_config_loader.py -v
```

## 📊 Exemplos de Cenários

### Cenário 1: Aumentar compensação para casos graves

Se casos de cobrança abusiva (Art. 71) estão muito baixos:

```json
"71": {
  "multiplier": 3.0,        // Era 2.0, agora 3x o valor
  "moral_damage_base": 8000.0  // Era 5000, agora R$ 8.000
}
```

### Cenário 2: Favorecer resolução extrajudicial

Para incentivar mais notificações extrajudiciais:

```json
"recommendation_base_scores": {
  "extrajudicial": {
    "base": 7.5,  // Era 6.0, agora mais favorável
    "max": 9.5
  }
}
```

### Cenário 3: Ajustar threshold de valor alto

Se casos acima de R$ 10.000 não são realmente "altos" na sua região:

```json
"high_value": {
  "threshold": 20000,  // Era 10000, agora R$ 20.000
  ...
}
```

## ⚠️ Cuidados

1. **Backup**: Sempre faça backup antes de editar
2. **JSON válido**: Use editor com validação JSON (VS Code, etc)
3. **Números**: Use ponto (.) para decimais, não vírgula
4. **Testes**: Rode testes após mudanças importantes
5. **Histórico**: Documente mudanças e motivo

## 🐛 Troubleshooting

### Erro: "JSON inválido"
- Verifique vírgulas, chaves e colchetes
- Use ferramenta online: https://jsonlint.com

### Erro: "Configuração não carregada"
- Verifique se o arquivo existe em `src/calculators/config/`
- Veja logs: `[CONFIG] ❌` indica erro

### Sistema voltou ao padrão
- JSON com erro → sistema usa `rules.py` como fallback
- Corrija o JSON e reinicie

## 📚 Documentação Técnica

Para detalhes de implementação, veja:
- `config_loader.py` - Código que carrega o JSON
- `estimator.py` - Como valores são calculados
- `scorer.py` - Como recommendations são rankeadas
- `tests/unit/test_config_loader.py` - Testes unitários

## 🔐 Segurança

- Não exponha este arquivo publicamente
- Use permissões adequadas no servidor: `chmod 640 rules_config.json`
- Em produção, considere usar variáveis de ambiente para valores sensíveis

---

**Versão**: 1.0.0
**Última atualização**: 2025-10-27
**Contato**: [Suporte Técnico]
