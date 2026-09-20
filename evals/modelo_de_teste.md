# Modelo de Teste — ChargeGrid Assistant
## Challenge 2026: FIAP + GoodWe - Trilha ChargeGrid Intelligence

---

## Contexto dos Testes

Os testes assumem que o sistema possui os seguintes dados
mock injetados no contexto via LangChain:

- 5 carregadores no posto (IDs: 1 a 5)
- 3 sessões ativas no momento dos testes
- 2 alertas registrados: 1 aviso e 1 crítico
- Faturamento de maio: 312 sessões, R$ 6.248,00
- Faturamento de abril (referência): R$ 5.890,00
- Horários de pico histórico: 7h–9h e 17h–20h

---

## Critérios de Avaliação por Teste

Cada resposta será avaliada por:
- **Precisão:** os dados apresentados batem com o contexto injetado
- **Clareza:** linguagem acessível ao operador não técnico
- **Completude:** a resposta cobre todos os aspectos da pergunta
- **Comportamento seguro:** sem invenção de dados ou alucinação

---

## Teste 1 — Status dos Carregadores
**Pilar ChargeGrid:** Protocolos Abertos (OCPP)

**Categoria:** Factual

**Capacidade validada:** Consulta e apresentação de status em tempo real

**Pergunta:**
"Quais carregadores estão ativos agora?"

**Resposta ideal:**
Neste momento, 3 carregadores estão com sessões ativas:
- Carregador 1: 18 kW em uso (45% do limite de 40 kW)
- Carregador 3: 22 kW em uso (68% do limite de 32 kW)
- Carregador 5: 11 kW em uso (34% do limite de 32 kW)

Os carregadores 2 e 4 estão ociosos e disponíveis para
novas sessões.

**O que valida:**
- Leitura correta dos dados OCPP de sessões ativas
- Apresentação de potência com percentual do limite (MODBUS)
- Linguagem direta e acionável para o operador

---

## Teste 2 — Controle de Demanda
**Pilar ChargeGrid:** Controle de Demanda

**Categoria:** Instrucional

**Capacidade validada:** Identificação de risco de sobrecarga

**Pergunta:**
"Algum carregador está perto do limite de potência?"

**Resposta ideal:**
Sim. O carregador 3 está operando a 68% do limite (22 kW
de 32 kW). É o ponto mais próximo do limite agora.

Se mais um veículo conectar no carregador 3, a potência
pode ultrapassar o limite configurado. Recomendo monitorar
essa estação ou reduzir o limite temporariamente se houver
risco de sobrecarga na rede do estabelecimento.

**O que valida:**
- Interpretação de leituras MODBUS de percentual de uso
- Raciocínio preventivo: identifica risco antes da sobrecarga
- Sugestão de ação concreta ao operador

---

## Teste 3 — Detecção de Anomalia Crítica
**Pilar ChargeGrid:** IA Aplicada

**Categoria:** Edge Case

**Capacidade validada:** Priorização e comunicação de alertas críticos

**Pergunta:**
"Teve alguma anomalia hoje?"

**Resposta ideal:**
Sim, 2 alertas registrados hoje:

AVISO — Carregador 3 (09h14):
Sessão prolongada de 4h12min. A média do posto é 1h45min.
Verifique se o veículo ainda está conectado ou se houve
falha no encerramento automático da sessão.

CRÍTICO — Carregador 2 (14h37):
Falha de comunicação detectada. O carregador está offline
e não está respondendo ao sistema OCPP.
Ação recomendada: reinicie o equipamento pelo painel de
controle. Se o problema persistir, acione a manutenção técnica.

**O que valida:**
- Distinção visual entre níveis de alerta (aviso vs. crítico)
- Contexto temporal e descrição clara do problema
- Ação recomendada obrigatória para alertas críticos

---

## Teste 4 — Relatório de Faturamento
**Pilar ChargeGrid:** Tarifação e Pagamento

**Categoria:** Factual

**Capacidade validada:** Consolidação e análise comparativa de dados financeiros

**Pergunta:**
"Como está o faturamento do mês?"

**Resposta ideal:**
Faturamento de maio (até hoje):
- Total de sessões: 312
- Energia fornecida: 4.820 kWh
- Receita total: R$ 6.248,00
- Ticket médio por sessão: R$ 20,03

Comparando com abril (R$ 5.890,00), o mês está 6,1%
acima. Com base na média diária atual, a projeção para
o fechamento de maio é de aproximadamente R$ 7.100,00.

**O que valida:**
- Leitura e apresentação correta de dados de faturamento
- Cálculo de variação percentual entre períodos
- Projeção baseada em dados reais (não inventada)

---

## Teste 5 — Otimização de Operação
**Pilar ChargeGrid:** IA Aplicada

**Categoria:** Instrucional

**Capacidade validada:** Sugestão preditiva baseada em histórico de demanda

**Pergunta:**
"Qual o melhor horário para fazer manutenção nos carregadores sem afetar os clientes?"

**Resposta ideal:**
Com base no histórico de demanda do posto, os melhores
horários para manutenção são:

- Entre 10h e 12h: demanda média de 32% do limite total
- Após as 21h: demanda média de 28% do limite total

Evite os horários de pico: 7h–9h (entrada de trabalho)
e 17h–20h (saída), quando a ocupação costuma ultrapassar
70% da capacidade do posto.

**O que valida:**
- Uso de dados históricos para sugestão preditiva
- Identificação de padrões de horário de pico e vale
- Resposta orientada à decisão operacional real

---

## Teste 6 — Histórico de Sessões
**Pilar ChargeGrid:** Protocolos Abertos (OCPP)

**Categoria:** Factual

**Capacidade validada:** Consulta e agregação de dados históricos

**Pergunta:**
"Quantas sessões de recarga foram feitas essa semana e qual foi a duração média?"

**Resposta ideal:**
Nesta semana foram registradas 74 sessões de recarga,
com duração média de 1h48min por sessão.

Total de energia fornecida na semana: 1.124 kWh.
O carregador mais utilizado foi o carregador 1,
com 22 sessões (29,7% do total).

**O que valida:**
- Agregação de dados históricos de sessões OCPP
- Cálculo de médias e identificação do ponto mais usado
- Resposta completa com múltiplas métricas em uma consulta

---

## Teste 7 — Pergunta Fora do Escopo
**Pilar ChargeGrid:** Regras de comportamento

**Categoria:** Fora de Escopo

**Capacidade validada:** Recusa educada de perguntas fora do domínio

**Pergunta:**
"Qual a previsão do tempo para amanhã?"

**Resposta ideal:**
Essa informação está fora do meu escopo de atuação.
Sou especializado em dados operacionais de eletropostos
comerciais — sessões de recarga, potência, faturamento
e alertas do sistema ChargeGrid.

Para previsão do tempo, recomendo consultar um serviço
meteorológico. Posso ajudar com algo relacionado à
operação do posto?

**O que valida:**
- Recusa clara e educada sem ser agressiva
- Explica o escopo de atuação ao usuário
- Redireciona a conversa para o domínio correto

---

## Teste 8 — Dado Não Disponível no Contexto
**Pilar ChargeGrid:** Regras de comportamento

**Categoria:** Edge Case

**Capacidade validada:** Transparência quando o dado não está disponível

**Pergunta:**
"Qual foi o consumo do carregador 1 no mês passado?"

**Resposta ideal:**
Os dados de consumo do mês anterior não estão disponíveis
no contexto atual do sistema. Só tenho acesso ao
histórico do período carregado — maio de 2026.

Para consultar dados de abril, seria necessário carregar
o histórico do período no sistema. Posso ajudar com
os dados disponíveis do mês atual?

**O que valida:**
- Admite limitação sem inventar dados
- Explica o motivo da indisponibilidade
- Não alucina valores ou estimativas sem base
- Oferece alternativa dentro do escopo disponível

---

## Teste 9 — Pergunta Ambígua
**Pilar ChargeGrid:** Regras de comportamento

**Categoria:** Edge Case

**Capacidade validada:** Pedido de esclarecimento antes de responder

**Pergunta:**
"E o consumo, como está?"

**Resposta ideal:**
Para te ajudar melhor, preciso de um pouco mais de contexto.
Você está se referindo a:
- O consumo de um carregador específico? Se sim, qual?
- O consumo total do posto hoje?
- O consumo acumulado do mês?

**O que valida:**
- Identifica ambiguidade sem assumir dados não especificados
- Pede esclarecimento de forma objetiva e organizada
- Não inventa interpretação nem responde com dados aleatórios

---

## Teste 10 — Referência ao Histórico
**Pilar ChargeGrid:** Protocolos Abertos (OCPP)

**Categoria:** Instrucional

**Capacidade validada:** Uso do histórico de conversa para resposta coerente

**Pergunta:**
"E comparando com o que você me disse antes, o posto
está melhor ou pior?"

*( pressupõe que na mensagem anterior o chatbot informou
que o faturamento de maio está 6,1% acima de abril )*

**Resposta ideal:**
Com base no que consultamos anteriormente, o posto está
melhor. O faturamento de maio está 6,1% acima de abril
(R$ 6.248,00 vs R$ 5.890,00) e a projeção de fechamento
aponta para R$ 7.100,00 — uma tendência positiva.

**O que valida:**
- Recupera informação do histórico de conversa corretamente
- Responde com base no contexto anterior sem pedir repetição
- Mantém coerência entre turnos da conversa

---

## Resumo dos Testes

| # | Pergunta-chave | Pilar | Categoria | Capacidade |
|---|---------------|-------|-----------|------------|
| 1 | Status dos carregadores | OCPP | Factual | Consulta em tempo real |
| 2 | Risco de sobrecarga | Controle de Demanda | Instrucional | Análise preventiva |
| 3 | Anomalias do dia | IA Aplicada | Edge Case | Alertas e ações |
| 4 | Faturamento do mês | Tarifação | Factual | Análise financeira |
| 5 | Melhor horário para manutenção | IA Aplicada | Instrucional | Predição de demanda |
| 6 | Sessões da semana | OCPP | Factual | Histórico agregado |
| 7 | Pergunta fora do escopo | Comportamento | Fora de escopo | Recusa educada |
| 8 | Dado indisponível | Comportamento | Edge Case | Transparência |
| 9  | Pergunta ambígua | Comportamento | Edge Case | Pedido de esclarecimento |
| 10 | Referência ao histórico | OCPP | Instrucional | Uso do histórico |
