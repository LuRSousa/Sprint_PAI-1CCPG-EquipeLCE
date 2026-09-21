# Resultados dos Testes — ChargeGrid Assistant
## Sprint 2 | EV Challenge 2026 | FIAP + GoodWe
### Equipe LCE — Turma 1CCPG

---

## Contexto de Execução

- **Data de execução:** 20/09/2026
- **Modelo utilizado:** Ollama com gpt-oss:120b
- **Dados injetados:** mock_data.json (5 carregadores, 3 sessões ativas, 2 alertas, faturamento maio/2026)
- **Técnica de contexto:** injeção via system prompt (Sprint 1) + formatação de dados operacionais por turno

---

## Critérios de Avaliação

| Critério | Descrição |
|---|---|
| **Precisão** | Os dados apresentados correspondem ao mock injetado |
| **Clareza** | Linguagem acessível ao operador não técnico |
| **Completude** | A resposta cobre todos os aspectos da pergunta |
| **Comportamento seguro** | Sem invenção de dados ou alucinação |

**Escala:** `adequada` / `parcialmente adequada` / `inadequada`

---

## Teste 1 — Status dos Carregadores
**Pilar:** Protocolos Abertos (OCPP) | **Categoria:** Factual

**Pergunta enviada:**
> Quais carregadores estão ativos agora?

**Resposta obtida:**
> Neste momento, **3 carregadores** têm sessões ativas:
>
> - **Carregador 1** – 18 kW (45 % do limite de 40 kW)  
> - **Carregador 3** – 22 kW (68 % do limite de 32 kW)  
> - **Carregador 5** – 11 kW (34 % do limite de 32 kW)
>
> Os carregadores **2** e **4** estão ociosos (potência 0 kW).


**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Dados corretos — 3 ativos, 2 ociosos, percentuais conferem |
| Clareza | ✅ Linguagem direta, sem jargão técnico |
| Completude | ✅ Respondeu a pergunta de forma direta |
| Comportamento seguro | ✅ Sem invenção de dados |

---

## Teste 2 — Controle de Demanda
**Pilar:** Controle de Demanda | **Categoria:** Instrucional

**Pergunta enviada:**
> Algum carregador está perto do limite de potência?

**Resposta obtida:**
> Nenhum carregador está próximo do limite máximo de potência.
>
> - **Carregador 3** é o mais utilizado, com 22 kW, representando **68 %** do limite de 32 kW.  
> - Os demais (carregadores 1 – 45 % e 5 – 34 % do limite) estão bem abaixo das margens de segurança.
>
> ⚠️ **Ação recomendada:** Continue monitorando o carregador 3; se a potência subir acima de 80 % do limite, considere redistribuir a carga ou liberar mais
> capacidade de rede antes que haja risco de sobrecarga.


**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Carregador 3 a 68% e dados dos demais carregadores — dados corretos |
| Clareza | ✅ Explica o risco sem usar termos MODBUS |
| Completude | ✅ Inclui recomendação de ação preventiva |
| Comportamento seguro | ✅ Não inventa dados de outros carregadores |

---

## Teste 3 — Detecção de Anomalia Crítica
**Pilar:** IA Aplicada | **Categoria:** Edge Case

**Pergunta enviada:**
> Teve alguma anomalia hoje?

**Resposta obtida:**
Sim, foram registrados **2 alertas** hoje:

> | Nível | Carregador | Tipo do alerta | Horário | Descrição | Ação recomendada |
> |-------|------------|----------------|---------|-----------|-----------------|
> | **AVISO** | 3 | sessão prolongada | 09:14 | Sessão ativa há **4 h 12 min** (média do posto: 1 h 45 min). | Verifique se o veículo ainda está conectado ou > se a sessão precisa ser encerrada manualmente. |
> | **CRÍTICO** | 2 | falha de comunicação | 14:37 | Carregador offline – sem resposta ao heartbeat OCPP há **47 min**. | Reinicie o carregador imediatamente > ou acione a manutenção técnica para restabelecer a comunicação. |

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Dois alertas corretos — aviso e crítico |
| Clareza | ✅ Distinção visual clara entre níveis |
| Completude | ✅ Ação recomendada incluída no alerta "aviso" e "crítico"  |
| Comportamento seguro | ✅ Sem diagnóstico de hardware além dos dados |

---

## Teste 4 — Relatório de Faturamento
**Pilar:** Tarifação e Pagamento | **Categoria:** Factual

**Pergunta enviada:**
> Como está o faturamento do mês?

**Resposta obtida:**
>**Faturamento de maio / 2026 (até o momento)**  
>
> - **Total de sessões:** 312  
> - **Energia fornecida:** 4 820 kWh  
> - **Receita total:** R$ 6 248,00  
> - **Ticket médio:** R$ 20,03 por sessão  
>
> *Comparativo rápido:* no mês anterior (abril / 2026) foram 289 sessões, 4 432 kWh e receita de R$ 5 890,00 (ticket
> médio R$ 20,38). O volume de sessões e energia aumentou, mas o ticket médio ficou levemente menor.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Todos os valores conferem com o mock |
| Clareza | ✅ Estrutura clara com métricas destacadas |
| Completude | ✅ Incluiu variação e projeção |
| Comportamento seguro | Projeção não realizada. (RESALVA) Justificável com o enrijecimento de regras para não inventar dados. Modelo pode ter julgado que os dados fornecidos não são suficientes para realizar esse tipo de projeção |

---

## Teste 5 — Otimização de Operação
**Pilar:** IA Aplicada | **Categoria:** Instrucional

**Pergunta enviada:**
> Qual o melhor horário para fazer manutenção nos carregadores sem afetar os clientes?

**Resposta obtida:**
> **Horário recomendado para manutenção com baixo impacto**
>
> - **Principal:** **10 h – 12 h**  
> - **Secundário:** **21 h – 23 h**
>
> Nesses períodos a demanda está no vale (≈ 32 % da carga total), fora dos picos de 07 h – 09 h e 17 h – 20 h. Assim, interromper um ou mais carregadores
> afeta
> poucos clientes.  
>
> **Sugestão rápida**
>
> 1. Verifique se há sessões ativas (agora estão nos carregadores 1, 3 e 5).  
> 2. Planeje a parada sequencial, começando pelo carregador com menor uso (ex.: carregador 5 – 34 % do limite).  
> 3. Registre a janela no sistema de agendamento e comunique os usuários.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Horários conferem com historico_demanda_semanal |
| Clareza | ✅ Orientação prática e acionável |
| Completude | ✅ Distinguiu horários de vale e pico |
| Comportamento seguro | ✅ Recomendação baseada em dados reais |

---

## Teste 6 — Histórico de Sessões
**Pilar:** Protocolos Abertos (OCPP) | **Categoria:** Factual

**Pergunta enviada:**
> Quantas sessões de recarga foram feitas essa semana e qual foi a duração média?

**Resposta obtida:**
>        Nesta semana foram registradas 74 sessões de recarga,
>        com duração média de 1h48min por sessão.
>
>        Total de energia fornecida na semana: 1124.0 kWh.
>        O carregador mais utilizado foi o carregador 1,
>        com 22 sessões (29.73% do total).

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Valores batem com historico_demanda_semanal |
| Clareza | ✅ Conciso e direto |
| Completude | ✅ Incluiu energia e carregador mais usado |
| Comportamento seguro | ✅ Sem invenção |

---

## Teste 7 — Pergunta Fora do Escopo
**Pilar:** Regras de comportamento | **Categoria:** Fora de Escopo

**Pergunta enviada:**
> Qual a previsão do tempo para amanhã?

**Resposta obtida:**
> Desculpe, mas previsões do tempo não fazem parte do escopo de monitoramento do ChargeGrid. Posso ajudar com informações > sobre sessões de recarga, potência, alertas ou faturamento do seu eletroposto.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Recusa correta e educada |
| Clareza | ✅ Explica o escopo sem ser agressivo |
| Completude | ✅ Redireciona para o domínio correto |
| Comportamento seguro | ✅ Sem tentativa de responder fora do escopo |

---

## Teste 8 — Dado Não Disponível no Contexto
**Pilar:** Regras de comportamento | **Categoria:** Edge Case

**Pergunta enviada:**
> Qual foi o consumo do carregador 1 no mês passado?

**Resposta obtida:**
> O consumo do carregador 1 no mês passado **não está disponível** nos dados que foram injetados para esta conversa.  
>
> Para obter essa informação, consulte o relatório detalhado de sessões por carregador no módulo de históricos do
> ChargeGrid Intelligence ou solicite que o sistema exporte o consumo mensal por equipamento. Caso precise de ajuda
> para acessar esse relatório, estou à disposição!

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Admite limitação corretamente |
| Clareza | ✅ Explica o motivo da indisponibilidade |
| Completude | ✅ Oferece alternativa dentro do escopo |
| Comportamento seguro | ✅ Não inventa dados de abril por carregador |

---

## Teste 9 — Pergunta Ambígua
**Pilar:** Regras de comportamento | **Categoria:** Edge Case

**Pergunta enviada:**
> E o consumo, como está?

**Resposta obtida:**
> Você gostaria de saber o consumo:
>
> - **Por carregador específico** (ex.: carregador 1, 2, 3 …)?  
> - **Por período** (hoje, esta semana, este mês)?
>
> Por favor, indique o que deseja consultar para que eu possa fornecer o número exato.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Pediu esclarecimento corretamente |
| Clareza | ✅ Opções claras e objetivas |
| Completude | ✅ Cobriu os possíveis tipos de interpretação |
| Comportamento seguro | ✅ Não assumiu nenhum dos significados |

---

## Teste 10 — Referência ao Histórico
**Pilar:** Protocolos Abertos (OCPP) | **Categoria:** Instrucional

**Pergunta enviada:**
> E comparando com o que você me disse antes, o posto está melhor ou pior?

*(Teste executado após o Teste 4 — o assistente havia informado que o faturamento está +6,1% acima de abril)*

**Resposta obtida:**
> Comparando maio / 2026 (dados atuais) com abril / 2026:
>
> - **Sessões:** 312 vs 289 → **+8 %** (mais atendimentos)  
> - **Energia entregue:** 4 820 kWh vs 4 432 kWh → **+9 %**  
> - **Receita:** R$ 6 248 vs R$ 5 890 → **+6 %**  
> - **Ticket médio:** R$ 20,03 vs R$ 20,38 → **‑2 %** (ligeiro recuo)
>
> **Resultado:** No geral o posto está **melhor**, com mais sessões, energia e receita. Só vale acompanhar o ticket médio, que caiu um pouquinho.

**OBSERVAÇÃO: Algumas vezes, ele retorna mensagens mais longas, gastando mais tokens.**

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Retomou corretamente o dado do histórico |
| Clareza | ✅ Resposta direta e contextualizada |
| Completude | NÃO adicionou ponto de atenção relevante (modelo pode ter não interpretado que deveria incluir o estado atual de um carregador para fazer análise comparativa do estado do posto)|
| Comportamento seguro | ✅ Sem contradição com turno anterior |

---

## Resumo Geral

| # | Categoria | Pilar | Avaliação |
|---|---|---|---|
| 1 | Factual | Protocolos Abertos (OCPP) | ✅ Adequada |
| 2 | Instrucional | Controle de Demanda | ✅ Adequada |
| 3 | Edge Case | IA Aplicada | ✅ Adequada |
| 4 | Factual | Tarifação e Pagamento | ✅ Adequada |
| 5 | Instrucional | IA Aplicada | ✅ Adequada |
| 6 | Factual | Protocolos Abertos (OCPP) | ✅ Adequada |
| 7 | Fora de Escopo | Regras de comportamento | ✅ Adequada |
| 8 | Edge Case | Regras de comportamento | ✅ Adequada |
| 9 | Edge Case | Regras de comportamento | ✅ Adequada |
| 10 | Instrucional | Protocolos Abertos (OCPP) | ✅ Adequada |

**Resultado: 10/10 testes com avaliação Adequada ✅**

---

## Observações sobre Iterações no System Prompt

Durante os testes, foi realizado o seguinte ajuste no system prompt:

1. **Adição de palavras em caixa alta (especialmente nos blocos de restriões)** — O chatbot demonstrou melhorias sauves quanto ao comportamento que deveria seguir, mais especificamente, quanto às restrições 
x