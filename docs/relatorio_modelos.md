# Relatório de Uso de Modelos e Parâmetros

## 1. Objetivo

Este relatório apresenta a comparação de diferentes modelos de
linguagem utilizados pelo ChargeGrid Assistant, avaliando também
o impacto dos parâmetros temperature, top_p e max_tokens.

O objetivo é observar diferenças de comportamento, precisão,
clareza, completude, segurança e desempenho entre as configurações.

---

## 2. Ambiente de Execução

- Projeto: ChargeGrid Assistant
- Framework: LangChain
- Plataforma: Ollama
- Dados utilizados: mock_data.json
- System prompt: versão X
- Data dos testes: XX/XX/2026

---

## 3. Modelos Avaliados

| Modelo | Parâmetros |
|---|---:|
| gpt-oss:120b | 120B |
| qwen3:8b | 8B |

---

## 4. Parâmetros de Inferência

| Configuração | Modelo | Temperature | Top-p | Max tokens |
|---|---|---:|---:|---:|
| A | gpt-oss:120b | 0.2 | 0.9 | 512 |
| B | gpt-oss:120b | 0.7 | 0.9 | 512 |
| C | qwen3:8b | 0.2 | 0.9 | 512 |
| D | qwen3:8b | 0.7 | 0.9 | 512 |

---

## 5. Metodologia

Todos os modelos foram submetidos às mesmas perguntas,
utilizando o mesmo system prompt e os mesmos dados mockados.

Foram avaliados testes relacionados a:

- consultas factuais;
- análise operacional;
- dados indisponíveis;
- perguntas ambíguas;
- perguntas fora do escopo;
- tentativas de jailbreak.

---

## 6. Resultados

### 6.1 Configuração A

Modelo: gpt-oss:120b

Temperature: 0.2  
Top-p: 0.9  
Max tokens: 512

#### Teste 1

Pergunta:

> ...

Resposta obtida:

> ...

Avaliação:

- Precisão: 2/2
- Clareza: 2/2
- Completude: 2/2
- Segurança: 2/2
- Latência: X s

Resultado: APROVADO

---

### 6.2 Configuração B

...

---

## 7. Comparação Consolidada

| Configuração | Aprovação | Precisão | Clareza | Completude | Segurança | Latência média |
|---|---:|---:|---:|---:|---:|---:|
| A | ... | ... | ... | ... | ... | ... |
| B | ... | ... | ... | ... | ... | ... |
| C | ... | ... | ... | ... | ... | ... |
| D | ... | ... | ... | ... | ... | ... |

---

## 8. Análise dos Resultados

### 8.1 Comparação entre modelos

[análise baseada nos resultados observados]

### 8.2 Impacto da temperature

[análise baseada nos resultados observados]

### 8.3 Impacto do top_p

[análise baseada nos resultados observados]

### 8.4 Impacto do max_tokens

[análise baseada nos resultados observados]

---

## 9. Considerações Finais

[conclusões baseadas nos dados obtidos]