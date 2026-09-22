# ChargeGrid Assistant - 1CCPG

## Challenge 2026: FIAP + GoodWe — Trilha ChargeGrid Intelligence

Chatbot com IA para operadores de eletropostos comerciais, capaz de orquestrar dados de potência, sessões e faturamento em linguagem natural.

---

## Integrantes

| Nome                                       | RM       | Turma |
| ------------------------------------------ | -------- | ----- |
| Caio Henrique Ferraz da Silva              | RM568992 | 1CCPG |
| Enzo Caruso Peter                          | RM570908 | 1CCPG |
| Leonardo Figueredo dos Santos              | RM573653 | 1CCPG |
| Leonardo Robert Maulicino                  | RM570329 | 1CCPG |
| Lucas Ramos de Sousa                       | RM573901 | 1CCPG |
| Matheus Pimenta Martini                    | RM569400 | 1CCPG |
| Pablo Renato dos Santos Sobral de Carvalho | RM569894 | 1CCPG |

---

## Problema Abordado

O problema central identificado é a ausência de mecanismos integrados em eletropostos comerciais para orquestrar potência, registrar ciclos de recarga, processar faturamento e comunicar eventos operacionais em tempo real.

Operadores de eletropostos comerciais lidam diariamente com dados técnicos brutos — sessões OCPP ativas, leituras MODBUS de potência e picos de demanda — sem uma camada de inteligência que traduza essas informações em decisões operacionais claras.

O resultado é maior dificuldade para acompanhar a operação, identificar anomalias e interpretar dados de consumo, sessões e faturamento.

---

## Proposta do Chatbot

O **ChargeGrid Assistant** é um assistente conversacional com IA que atua como camada de interpretação sobre os dados operacionais de um eletroposto comercial no ecossistema GoodWe/FIAP.

Ele permite que o operador faça perguntas em linguagem natural e receba respostas contextualizadas com base nos dados disponíveis do sistema de recarga.

O chatbot não substitui o painel técnico. Ele o complementa, transformando informações operacionais em respostas mais acessíveis para o operador.

Entre os dados considerados pelo sistema estão:

* Status dos carregadores;
* Potência e consumo;
* Sessões de recarga;
* Alertas e anomalias;
* Informações de faturamento;
* Eventos operacionais;
* Dados associados aos protocolos OCPP e MODBUS.

---

## Persona do Usuário

**Operador comercial do eletroposto:** dono do estabelecimento, gerente ou atendente treinado.

Perfil: responsável pela operação do ponto de recarga comercial. Não necessariamente possui formação técnica, mas precisa tomar decisões rápidas relacionadas à operação, potência, sessões e faturamento.

### Necessidades atendidas

* Consultar status atual dos carregadores;
* Verificar sessões em andamento;
* Consultar consumo de energia;
* Identificar alertas ou anomalias;
* Consultar histórico de sessões;
* Analisar informações de faturamento;
* Interpretar eventos registrados pelo sistema;
* Obter informações operacionais em linguagem natural.

---

## Contexto: ChargeGrid Intelligence

Trilha presencial do EV Challenge 2026, com foco na gestão comercial de eletropostos públicos, controle de demanda e operação em tempo real.

### Os 4 pilares do ChargeGrid

1. **Controle de Demanda** — gerenciamento da potência entregue;
2. **Tarifação e Pagamento** — cobrança dinâmica via APIs;
3. **Protocolos Abertos** — integração OCPP e MODBUS;
4. **IA Aplicada** — previsão de picos e análise de sessões.

O ChargeGrid Assistant atua principalmente no pilar de **IA Aplicada**, utilizando os dados dos demais componentes para fornecer uma interface conversacional ao operador.

---

# Sprint 3 — Evolução com LangChain

Na Sprint 3, o chatbot foi refatorado para incorporar conceitos de **LangChain, LCEL, memória conversacional, saída estruturada, engenharia de contexto e guardrails**.

A arquitetura passou a separar o processamento das perguntas em diferentes etapas.

### Fluxo principal

```text
Pergunta do operador
        │
        ▼
   Guardrails
        │
        ▼
      Router
        │
   ┌────┴────┐
   │         │
   ▼         ▼
Não       Estruturada
estruturada    │
   │            ▼
   │       Pydantic v2
   │            │
   ▼            ▼
LCEL +       Resposta
memória      estruturada
   │
   ▼
Resposta ao operador
```

---

## LCEL

A geração das respostas não estruturadas utiliza **LangChain Expression Language (LCEL)** para composição da cadeia:

```text
ChatPromptTemplate
        │
        ▼
    ChatOllama
        │
        ▼
  StrOutputParser
```

Na implementação, a composição é realizada por meio do operador `|`:

```python
chain = prompt | llm | parser
```

Essa estrutura separa a construção do prompt, a inferência do modelo e o processamento da saída.

---

## Router de Consultas

Antes da geração da resposta, a pergunta passa por um router que classifica a solicitação em duas categorias:

* `estruturada`
* `nao_estruturada`

As consultas estruturadas são direcionadas para uma cadeia específica com saída Pydantic.

As demais consultas utilizam a cadeia conversacional principal.

O router possui regras específicas para evitar que perguntas fora do conjunto de dados estruturados sejam direcionadas incorretamente para o schema.

Quando existe dúvida sobre a classificação, a orientação do prompt é utilizar a categoria `nao_estruturada`.

---

## Memória Conversacional

A Sprint 3 passou a utilizar:

* `RunnableWithMessageHistory`;
* `ConversationTokenBufferMemory`;
* sessões independentes identificadas por `session_id`;
* limite configurado de **2300 tokens** para o buffer de memória.

A memória é associada à sessão atual do usuário.

Isso permite que perguntas posteriores utilizem informações presentes em turnos anteriores da conversa.

Exemplo:

```text
Operador:
Qual é o status dos carregadores?

Operador:
E qual deles está consumindo mais energia?

Operador:
E aquele primeiro carregador, qual é a situação dele?
```

O histórico é mantido durante a sessão ativa da aplicação.

---

## Saída Estruturada com Pydantic v2

Consultas relacionadas aos dados estruturados de sessões semanais utilizam um schema desenvolvido com **Pydantic v2**.

O schema `ConsultaSessoesSemana` representa informações como:

* número de sessões;
* duração média;
* energia fornecida;
* carregador mais utilizado;
* número de sessões do carregador mais utilizado;
* percentual de sessões.

O projeto também utiliza `field_validator` para validar valores específicos do domínio.

Exemplo:

```python
@field_validator("carregador_mais_usado")
@classmethod
def validar_carregador(cls, carregador):
    if carregador is not None and (carregador < 1 or carregador > 5):
        raise ValueError("ID de carregador inválido")
    return carregador
```

Também existe validação do percentual de sessões, garantindo valores entre 0 e 100.

---

## Engenharia de Contexto

O sistema utiliza um **System Prompt versionado**, com organização das instruções por contexto.

O prompt utiliza marcação XML para separar informações e instruções do sistema.

Entre os elementos considerados estão:

* identidade do assistente;
* escopo operacional;
* contexto do eletroposto;
* dados disponíveis;
* comportamento esperado;
* restrições;
* regras de resposta;
* prevenção de alucinações.

O contexto operacional é inserido na cadeia junto aos dados disponíveis para a consulta.

---

## Medição de Tokens

O projeto utiliza **tiktoken** para medir a quantidade de tokens utilizada durante o processamento.

São considerados indicadores como:

* tokens de entrada;
* tokens de saída;
* tokens utilizados pelo router;
* quantidade total de tokens;
* latência do router;
* latência da geração da resposta;
* latência total.

Essas métricas permitem comparar o comportamento dos modelos e acompanhar o custo computacional das consultas.

---

## Guardrails e Segurança

O chatbot possui uma camada de validação para impedir comportamentos fora do escopo definido para o projeto.

### Prompt Injection e Jailbreak

Perguntas que tentam alterar as instruções originais do sistema, ignorar regras ou manipular o comportamento do modelo são bloqueadas.

### Validação de Escopo GoodWe

O sistema verifica se a solicitação está relacionada ao domínio operacional do ChargeGrid/GoodWe.

Solicitações fora do escopo definido são recusadas de forma controlada.

### Especificações de produto

O chatbot não deve inventar especificações técnicas de equipamentos quando a informação não estiver disponível no contexto fornecido.

### Segurança elétrica

Orientações que exigiriam diagnóstico físico ou intervenção elétrica são tratadas com restrição, evitando que o chatbot apresente uma resposta operacional como substituição de um profissional qualificado.

---

# Tecnologias Selecionadas

| Tecnologia       | Papel no projeto                       |
| ---------------- | -------------------------------------- |
| Python 3.11+     | Linguagem principal                    |
| LangChain        | Orquestração das chains e memória      |
| LCEL             | Composição das cadeias                 |
| LangChain Ollama | Integração com modelos Ollama          |
| Ollama           | Execução/inferência dos modelos        |
| GPT-OSS 120B     | Modelo principal de linguagem          |
| Pydantic v2      | Validação e saída estruturada          |
| Streamlit        | Interface conversacional web           |
| tiktoken         | Medição de tokens                      |
| python-dotenv    | Gerenciamento de variáveis de ambiente |
| JSON             | Dados operacionais simulados           |

---

## Justificativa Técnica

### Por que LangChain?

O LangChain foi utilizado na Sprint 3 para estruturar o fluxo de processamento das perguntas e aplicar conceitos de LCEL, memória conversacional e saída estruturada.

A utilização de componentes separados permite organizar o sistema em etapas:

```text
Prompt → Modelo → Parser
```

Além disso, `RunnableWithMessageHistory` permite associar o histórico conversacional a sessões independentes.

### Por que Ollama?

O Ollama foi escolhido como camada de acesso aos modelos de linguagem, permitindo utilizar modelos compatíveis tanto em execução local quanto através do Ollama Cloud.

Essa abordagem mantém flexibilidade para testes com diferentes modelos sem alterar a arquitetura principal do chatbot.

### Por que Streamlit?

O Streamlit permite construir a interface conversacional utilizando Python, sem a necessidade de manter um frontend separado.

A aplicação oferece:

* interface de chat;
* histórico da conversa;
* criação de nova conversa;
* visualização de métricas;
* exportação das mensagens.

### Por que Pydantic?

O Pydantic permite definir um contrato explícito para respostas estruturadas e validar os valores produzidos pelo modelo.

Isso reduz a dependência de respostas exclusivamente textuais quando a aplicação precisa trabalhar com dados estruturados.

### Por que tiktoken?

O `tiktoken` é utilizado para acompanhar o volume de tokens das entradas e saídas e auxiliar na análise de eficiência do contexto utilizado pelo chatbot.

---

# Segurança de Configuração

As credenciais utilizadas pela aplicação são carregadas através de variáveis de ambiente.

Exemplo:

```env
OLLAMA_API_KEY=sua_chave_aqui
OLLAMA_MODEL=gpt-oss:120b
OLLAMA_MODEL_ROUTER=seu_modelo_do_router
```

O arquivo `.env` **não deve ser versionado**.

O repositório disponibiliza `.env.example` como referência para configuração.

---

# 📂 Estrutura do Projeto

```text
ChargeGrid-Assistant/
│
├── .gitignore
├── .env.example
├── README.md
├── requirements.txt
│
├── src/
│   ├── app.py
|   ├── recursos.py
|   |
│   ├── chain/
│   │   ├── builder.py
│   │   ├── memoria.py
│   │   ├── router.py
│   │   └── structured_builder.py
│   │
│   ├── guardrails/
│   │   ├── moderation.py
│   │   ├── scope_validator.py
│   |   └── ResultadoGuardrail.py
│   │
│   └── schemas/
│       └── consulta_recarga.py
│
├── data/
│   └── mock_data.json
│
├── prompts/
│   ├── router_system_prompts/
│   |   ├── router_system_prompt_v1.md
|   |   └── router_system_prompt_v2.md
|   |
|   ├── system_prompts/
│   |   ├── system_prompt_v1.md
|   |   └── system_prompt_v2.md
|   |
|   └── tabela_comparativa.md
│
├── evals/
│   ├── modelo_de_teste_v1.md
│   ├── modelo_de_teste_v2.md
│   ├── resultado_de_teste_v1.md
│   ├── resultado_de_teste_v2.md
│   └── sprint3_results.json
|
└── docs/
    ├── fluxograma.png
    └── relatorio_modelos.md
```

> A estrutura acima representa os principais componentes da aplicação. Arquivos adicionais de documentação e avaliação podem estar presentes no repositório conforme a evolução do projeto.

---

# 📂 Arquivos e Documentação

* [Fluxograma](docs/fluxograma.png)
* [Relatório de evolução do projeto](docs/relatorio_evolucao.pdf)
* [System Prompt](prompts/system_prompt.md)
* [Dados mock](data/mock_data.json)
* [Aplicação Streamlit](src/app.py)
* [Builder principal](src/chain/builder.py)
* [Memória conversacional](src/chain/memoria.py)
* [Router](src/chain/router.py)
* [Chain estruturada](src/chain/structured_builder.py)
* [Schema Pydantic](src/schemas/consulta_recarga.py)
* [Guardrails](src/guardrails/)
* [Testes](tests/)
* [Avaliações](evals/)
* [Documentação](docs/)
* [Requisitos](requirements.txt)
* [Exemplo de configuração](.env.example)

---

# Instalação e Execução

## Pré-requisitos

* Python 3.11 ou superior;
* Pip;
* acesso ao Ollama ou Ollama Cloud;
* chave de API do Ollama quando utilizada a infraestrutura em nuvem.

## 1. Clone o repositório

```bash
git clone https://github.com/LuRSousa/Sprint_PAI-1CCPG-EquipeLCE.git
cd Sprint_PAI-1CCPG-EquipeLCE
```

## 2. Crie um ambiente virtual

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/Mac

```bash
source venv/bin/activate
```

## 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## 4. Configure as variáveis de ambiente

Copie:

```text
.env.example
```

para:

```text
.env
```

Configure a chave da Ollama:

```env
OLLAMA_API_KEY=sua_chave_aqui
```

Configure também os modelos utilizados pela aplicação conforme as variáveis disponíveis no `.env.example`.

> O arquivo `.env` não deve ser commitado.

## 5. Execute a aplicação

```bash
streamlit run src/app.py
```

Caso o comando `streamlit` não esteja disponível no PATH:

```bash
python -m streamlit run src/app.py
```

---

# Testes

## Testes da Sprint 2

Foram executados 10 casos de teste planejados anteriormente, cobrindo:

* Status dos carregadores;
* Controle de demanda;
* Detecção de anomalias;
* Relatório de faturamento;
* Otimização de horários para manutenção;
* Histórico de sessões;
* Recusa de perguntas fora do escopo;
* Transparência com dados não disponíveis;
* Perguntas ambíguas;
* Referência ao histórico da conversa.

---

## Avaliação da Sprint 3

A Sprint 3 adicionou uma nova camada de avaliação sobre o comportamento do chatbot.

Os testes consideram aspectos como:

* classificação pelo router;
* respostas estruturadas;
* validação Pydantic;
* memória conversacional;
* comportamento após múltiplos turnos;
* proteção contra prompt injection/jailbreak;
* validação do escopo GoodWe;
* tratamento de informações não disponíveis;
* utilização de tokens;
* latência das chamadas.

Os resultados consolidados da avaliação são mantidos na pasta `evals/`.

---

# Vídeo Demonstrativo - Sprint 2

[Vídeo demonstrativo no YouTube](https://youtu.be/i_Y-zGGlqRM)

O vídeo apresenta o chatbot em funcionamento e demonstra sua utilização no contexto do EV Challenge 2026.

>Obs: O vídeo representa a versão da sprint 2 do projeto pois era um dos entregáveis necessários anteriormente.

---

# Limitações Conhecidas

### Dados simulados

O chatbot atualmente utiliza dados simulados em JSON. A integração completa com APIs reais do ChargeGrid/GoodWe não foi implementada nesta etapa.

### Sem ações automáticas

O chatbot atua como camada de consulta e interpretação. Ele não executa diretamente ações físicas nos carregadores, como:

* ligar ou desligar carregadores;
* alterar potência;
* iniciar ou encerrar sessões;
* realizar manutenção.

### Histórico volátil

O histórico conversacional é mantido durante a sessão ativa da aplicação.

As conversas não são persistidas como histórico permanente após o encerramento da sessão.

### Dependência do modelo

A qualidade das respostas pode variar conforme o modelo LLM utilizado, especialmente em tarefas que exigem interpretação contextual ou geração de respostas em português.

### Dados operacionais

As respostas são limitadas aos dados disponibilizados no contexto da aplicação. O chatbot não deve inventar informações que não estejam presentes nos dados fornecidos.

---

# Evolução da Arquitetura

A principal evolução entre as versões anteriores e a Sprint 3 foi a transição de um chatbot baseado em chamadas diretas ao modelo para uma arquitetura organizada em componentes de processamento.

```text
ANTES

Usuário
   │
   ▼
Chatbot
   │
   ▼
LLM
   │
   ▼
Resposta
```

```text
SPRINT 3

Usuário
   │
   ▼
Guardrails
   │
   ▼
Router
   │
   ├───────────────┐
   ▼               ▼
Estruturada    Não estruturada
   │               │
   ▼               ▼
Pydantic       LCEL + Memória
   │               │
   └───────┬───────┘
           ▼
        Resposta
```

Essa separação permite controlar melhor o fluxo de informações, validar respostas estruturadas, preservar contexto conversacional e aplicar regras de segurança antes e durante o processamento.
