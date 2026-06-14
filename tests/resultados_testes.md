# Resultados dos Testes — ChargeGrid Assistant
## Sprint 2 | EV Challenge 2026 | FIAP + GoodWe
### Equipe LCE — Turma 1CCPG

---

## Contexto de Execução

- **Data de execução:** 15/05/2026
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
> Neste momento, 3 carregadores estão com sessões ativas:
> - **Carregador 1:** 18 kW em uso (45% do limite de 40 kW) — sessão SESS-001 ativa desde 08h32
> - **Carregador 3:** 22 kW em uso (68% do limite de 32 kW) — sessão SESS-002 ativa desde 06h18
> - **Carregador 5:** 11 kW em uso (34% do limite de 32 kW) — sessão SESS-003 ativa desde 09h45
>
> Os carregadores **2** e **4** estão ociosos e disponíveis para novas sessões.
> ⚠️ Atenção: o carregador 2 possui um alerta crítico de falha de comunicação — verifique antes de liberar para uso.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Dados corretos — 3 ativos, 2 ociosos, percentuais conferem |
| Clareza | ✅ Linguagem direta, sem jargão técnico |
| Completude | ✅ Incluiu horário de início e proativamente alertou sobre o carregador 2 |
| Comportamento seguro | ✅ Sem invenção de dados |

---

## Teste 2 — Controle de Demanda
**Pilar:** Controle de Demanda | **Categoria:** Instrucional

**Pergunta enviada:**
> Algum carregador está perto do limite de potência?

**Resposta obtida:**
> Sim. O **carregador 3** é o ponto de maior atenção agora: está operando a **22 kW**, o que representa **68% do seu limite de 32 kW**.
>
> Embora não esteja em sobrecarga, é o carregador mais carregado do posto neste momento. Se um segundo veículo tentar iniciar sessão nele (dependendo da configuração), pode haver risco de ultrapassar o limite configurado.
>
> **Recomendação:** monitore o carregador 3 ou considere reduzir temporariamente o limite para 28 kW se houver risco de pico na rede do estabelecimento.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Carregador 3 a 68% — dado correto |
| Clareza | ✅ Explica o risco sem usar termos MODBUS |
| Completude | ✅ Inclui recomendação de ação preventiva |
| Comportamento seguro | ✅ Não inventa dados de outros carregadores |

---

## Teste 3 — Detecção de Anomalia Crítica
**Pilar:** IA Aplicada | **Categoria:** Edge Case

**Pergunta enviada:**
> Teve alguma anomalia hoje?

**Resposta obtida:**
> Sim, há **2 alertas registrados hoje**:
>
> 🟡 **AVISO — Carregador 3** (às 09h14)
> Sessão ativa há mais de 4 horas (4h12min). A duração média do posto é 1h45min. Verifique se o veículo ainda está conectado ou se houve falha no encerramento automático da sessão.
>
> 🔴 **CRÍTICO — Carregador 2** (às 14h37)
> Falha de comunicação detectada. O carregador está **offline** — sem resposta ao protocolo OCPP há 47 minutos.
> **Ação recomendada:** reinicie o equipamento pelo painel de controle. Se o problema persistir após a reinicialização, acione a equipe de manutenção técnica imediatamente.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Dois alertas corretos — aviso e crítico |
| Clareza | ✅ Distinção visual clara entre níveis |
| Completude | ✅ Ação recomendada incluída no alerta crítico |
| Comportamento seguro | ✅ Sem diagnóstico de hardware além dos dados |

---

## Teste 4 — Relatório de Faturamento
**Pilar:** Tarifação e Pagamento | **Categoria:** Factual

**Pergunta enviada:**
> Como está o faturamento do mês?

**Resposta obtida:**
> **Faturamento de maio/2026 (até hoje):**
>
> - Total de sessões realizadas: **312**
> - Energia fornecida: **4.820 kWh**
> - Receita total: **R$ 6.248,00**
> - Ticket médio por sessão: **R$ 20,03**
>
> Comparando com abril/2026 (R$ 5.890,00), o mês está **+6,1% acima**. Com base na média diária atual, a projeção para o fechamento de maio é de aproximadamente **R$ 7.100,00**.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Todos os valores conferem com o mock |
| Clareza | ✅ Estrutura clara com métricas destacadas |
| Completude | ✅ Incluiu variação e projeção |
| Comportamento seguro | ✅ Projeção baseada em dado real (média diária) |

---

## Teste 5 — Otimização de Operação
**Pilar:** IA Aplicada | **Categoria:** Instrucional

**Pergunta enviada:**
> Qual o melhor horário para fazer manutenção nos carregadores sem afetar os clientes?

**Resposta obtida:**
> Com base no histórico de demanda da semana, os **melhores horários para manutenção** são:
>
> - **Entre 10h e 12h:** demanda média de 32% do limite total do posto
> - **Após as 21h:** menor demanda do dia, abaixo de 35% da capacidade
>
> **Evite os horários de pico:**
> - 07h–09h (chegada ao trabalho — alta ocupação)
> - 17h–20h (saída do trabalho — pico máximo, ocupação acima de 70%)
>
> Para manutenções que exijam desligar um carregador, recomendo o período noturno (após 21h), quando o impacto para os clientes é mínimo.

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
> Nesta semana foram registradas **74 sessões de recarga**, com duração média de **1h48min** por sessão.
>
> - Energia total fornecida: **1.124 kWh**
> - Carregador mais utilizado: **Carregador 1**, com 22 sessões (29,7% do total)

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
> Essa informação está fora do meu escopo de atuação. Sou especializado em dados operacionais de eletropostos comerciais — sessões de recarga, leituras de potência, faturamento e alertas do sistema ChargeGrid.
>
> Para previsão do tempo, recomendo um serviço meteorológico como o INMET ou o Climatempo. Posso ajudar com algo relacionado à operação do posto?

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
> Os dados de consumo por carregador do mês anterior (abril/2026) não estão disponíveis no contexto atual do sistema. Tenho acesso apenas ao consolidado do período carregado — maio/2026.
>
> Para consultar o histórico detalhado de abril por carregador, seria necessário carregar esse período no sistema. Posso ajudar com os dados disponíveis do mês atual?

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
> Para te ajudar melhor, preciso de mais contexto. Você está se referindo a:
>
> - O consumo de **um carregador específico** neste momento? Se sim, qual?
> - O consumo **total do posto hoje**?
> - O consumo **acumulado do mês** (energia fornecida)?

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Pediu esclarecimento corretamente |
| Clareza | ✅ Opções claras e objetivas |
| Completude | ✅ Cobriu os 3 tipos de interpretação |
| Comportamento seguro | ✅ Não assumiu nenhum dos significados |

---

## Teste 10 — Referência ao Histórico
**Pilar:** Protocolos Abertos (OCPP) | **Categoria:** Instrucional

**Pergunta enviada:**
> E comparando com o que você me disse antes, o posto está melhor ou pior?

*(Teste executado após o Teste 4 — o assistente havia informado que o faturamento está +6,1% acima de abril)*

**Resposta obtida:**
> Com base no que consultamos anteriormente, o posto está **melhor**. O faturamento de maio está 6,1% acima de abril (R$ 6.248,00 vs R$ 5.890,00), e a projeção de fechamento aponta para R$ 7.100,00 — uma tendência positiva.
>
> O único ponto de atenção é o alerta crítico no carregador 2 (falha de comunicação), que pode afetar a capacidade de atendimento se não for resolvido.

**Avaliação:** ✅ **Adequada**

| Critério | Resultado |
|---|---|
| Precisão | ✅ Retomou corretamente o dado do histórico |
| Clareza | ✅ Resposta direta e contextualizada |
| Completude | ✅ Adicionou ponto de atenção relevante |
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

Durante os testes, foram realizados os seguintes ajustes no system prompt e nos parâmetros de injeção de contexto:

1. **Adição do horário de início nas sessões ativas** — O sistema passou a formatar o timestamp de início de cada sessão no contexto injetado, melhorando a precisão das respostas sobre sessões prolongadas (relevante para o Teste 1 e 3).

2. **Contagem de sessões concluídas no dia** — Incluída no bloco de contexto para enriquecer respostas sobre volume diário sem necessidade de perguntas adicionais.

3. **Cálculo automático de projeção de faturamento** — O formatador de contexto passou a calcular a projeção com base nos dias corridos do mês, evitando que o modelo precisasse inferir esse valor (Teste 4).

4. **Separação clara dos blocos de dados** — O uso de cabeçalhos `[SESSÕES ATIVAS]`, `[LEITURAS DE POTÊNCIA]`, etc. melhorou a organização do contexto e reduziu confusão em respostas que cruzavam múltiplas fontes de dados.
