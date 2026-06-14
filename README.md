# ChargeGrid Assistant - 1CCPG
## Challenge 2026: FIAP + GoodWe - Trilha ChargeGrid Intelligence

Chatbot com IA para operadores de eletropostos comerciais —
orquestrando dados de potência, sessões e faturamento em
linguagem natural.

---

## Integrantes

| Nome | RM | Turma |
|------|----|-------|
| Caio Henrique Ferraz da Silva | RM568992 | 1CCPG |
| Enzo Caruso Peter | RM570908 | 1CCPG |
| Leonardo Figueredo dos Santos | RM573653 | 1CCPG |
| Leonardo Robert Maulicino | RM570329 | 1CCPG |
| Lucas Ramos de Sousa | RM573901 | 1CCPG |

---

## Problema Abordado

O problema central identificado é a ausência de mecanismos integrados 
em eletropostos comerciais para orquestrar potência, registrar ciclos 
de recarga, processar faturamento e comunicar eventos operacionais em tempo real.

Operadores de eletropostos comerciais lidam diariamente com dados
técnicos brutos — sessões OCPP ativas, leituras MODBUS de potência,
picos de demanda — sem uma camada de inteligência que traduza essas
informações em decisões operacionais claras. O resultado é ineficiência
energética, falhas não detectadas a tempo e dificuldade de precificação
dinâmica.

---

## Proposta do Chatbot

O **ChargeGrid Assistant** é um agente conversacional com IA que
atua como assistente operacional de eletropostos comerciais no
ecossistema GoodWe/FIAP. Ele traduz dados técnicos de recarga —
gerados pelos protocolos OCPP e MODBUS — em respostas claras e
acionáveis para o operador do posto.

O chatbot não substitui o painel técnico: ele complementa,
permitindo que operadores façam perguntas em linguagem natural
e recebam respostas contextualizadas com base nos dados reais
do sistema de recarga.

---

## Persona do Usuário

**Operador comercial do eletroposto:** Dono do estabelecimento, gerente ou atendente
treinado.

Perfil: responsável pela operação do ponto de recarga comercial.
Não necessariamente técnico, mas precisa tomar decisões rápidas
sobre potência, faturamento e manutenção.

Necessidades atendidas pelo chatbot:

- Consultar status atual dos carregadores (ativo, ocioso, com falha)
- Verificar sessões em andamento e consumo kWh em tempo real
- Identificar alertas de sobrecarga ou anomalia de consumo
- Consultar histórico de sessões e dados de faturamento
- Entender picos de demanda e receber sugestões de otimização
- Verificar eventos registrados via protocolo OCPP

---

## Contexto: ChargeGrid Intelligence

Trilha presencial do EV Challenge 2026. Foco em gestão comercial
de eletropostos públicos (shoppings, postos, estacionamentos, frotas), 
controle de demanda e operação em tempo real.

Os 4 pilares do ChargeGrid:

1. **Controle de Demanda** — gerenciamento da potência entregue
2. **Tarifação e Pagamento** — cobrança dinâmica via APIs
3. **Protocolos Abertos** — integração OCPP e MODBUS
4. **IA Aplicada** — previsão de picos e análise de sessões

O ChargeGrid Assistant implementa o pilar de IA Aplicada: traduz
os dados brutos dos outros três pilares em linguagem natural
acessível ao operador.

---

## Tecnologias Selecionadas

| Tecnologia         | Versão       | Papel no projeto                          |
|--------------------|--------------|-------------------------------------------|
| Python             | 3.11+        | Linguagem principal                       |
| Ollama             | 0.3+         | Execução de modelos LLM (local ou nuvem)  |
| GPT-OSS            | 120b         | Modelo de linguagem (inferência)          |
| Streamlit          | 1.35+        | Interface conversacional web              |
| JSON (mock)        | —            | Dados simulados de sessões OCPP e potência |
| python-dotenv      | 1.0+         | Gerenciamento de variáveis de ambiente    |

---

## Justificativa Técnica

**Por que Ollama?**
O Ollama foi escolhido por permitir execução **local** (gratuita, sem dependência de APIs externas) ou em **nuvem** com chave API, oferecendo flexibilidade total. Ele suporta modelos modernos como `gemma3:4b` e `gpt-oss:120b`, com bom desempenho em português. Diferente de soluções como Gemini ou GPT-4, o Ollama não exige cartão de crédito para começar e pode ser usado offline.

**Por que Streamlit?**
Streamlit permite prototipar a interface conversacional em Python puro, sem frontend separado. É rápido, interativo e listado como diferencial técnico no challenge.

**Por que python-dotenv?**
Para carregar configurações sensíveis (como `OLLAMA_API_KEY` ou `OLLAMA_HOST`) de um arquivo `.env` que **nunca é commitado**, garantindo segurança.

**Alternativas consideradas e descartadas:**
- *Google Gemini:* dependência de nuvem e chave de API obrigatória; risco de custos ou exposição da chave.
- *OpenAI GPT-4o:* excelente qualidade, mas API paga — incompatível com a regra de gratuidade da disciplina.
- *Ollama local apenas:* o grupo optou por manter compatibilidade com nuvem também, através de variáveis de ambiente.

---

## 📂 Acesse os arquivos do repositório

- [Fluxograma](docs/fluxograma.png)
- [System Prompt](prompts/system_prompt.md)
- [Dados mock](data/mock_data.json)
- [Código principal - app.py](src/app.py)
- [Lógica do chatbot - chatbot.py](src/chatbot.py)
- [Modelo de testes](tests/modelo_de_teste.md)
- [Resultados dos testes](tests/resultados_testes.md)
- [Requisitos](requirements.txt)
- [Exemplo de configuração](.env.example)

---

## Instalação e Execução

### Pré-requisitos
- Python 3.11 ou superior
- Pip (gerenciador de pacotes)
- (Opcional) Ollama instalado localmente – [ollama.com/download](https://ollama.com/download)

### Passo a passo

1. **Clone o repositório**
  ```bash
    git clone https://github.com/SEU_USUARIO/ChargeGrid-Assistant.git
  ```

2. **Crie e ative um ambiente virtual**
  ```bash
    python -m venv venv
  ```

  ```bash
    source venv/bin/activate      # Linux/Mac
    venv\Scripts\activate         # Windows
  ```

3. **Adicione a chave API**
  - Copie o arquivo **.env.example** para um **.env**
  - Coloque sua chave API em: OLLAMA_API_KEY=shua_chave_aqui
  > Atenção: O arquivo .env nunca deve ser commitado – ele está no .gitignore.

4. **Execute o chatbot**
  ```bash
    streamlit run src/app.py
  ```

  se o streamlit não estiver no PATH:
  ```bash
    python -m streamlit run src/app.py
  ```

---

## Estrutura do Projeto

```plaintext
ChargeGrid-Assistant/
├── .gitignore
├── .env.example
├── README.md
├── requirements.txt
├── src/
│   ├── app.py
│   └── chatbot.py
├── data/
│   └── mock_data.json
├── prompts/
│   └── system_prompt.md
├── tests/
│   ├── modelo_de_teste.md
│   └── resultados_testes.md
└── docs/
    └── fluxograma.png
```

---

## Testes Realizados (Sprint 2)

Foram executados 10 casos de teste conforme planejado na Sprint 1, utilizando o modelo gpt-oss:120b (Ollama). Todos os testes foram avaliados como adequados, cobrindo:

- Status dos carregadores (OCPP)
- Controle de demanda (risco de sobrecarga)
- Detecção de anomalias críticas
- Relatório de faturamento e projeção
- Otimização de horários para manutenção
- Histórico de sessões
- Recusa de perguntas fora do escopo
- Transparência com dados não disponíveis
- Perguntas ambíguas
- Referência ao histórico da conversa

---

## Vídeo Demonstrativo


O vídeo mostra o chatbot em funcionamento, com pelo menos três interações relevantes ao contexto do EV Challenge 2026.

---

## Limitações conhecidas

- **Dados mock:** o chatbot opera com dados simulados (JSON). A integração com APIs reais do ChargeGrid/GoodWe não foi implementada nesta sprint.
- **Sem ações automáticas:** o chatbot apenas consulta e orienta – não liga/desliga carregadores, não ajusta potência, não agenda manutenção.
- **Histórico volátil:** o contexto de conversa é mantido apenas durante a sessão ativa do Streamlit. Conversas anteriores não são persistidas.
- **Dependência de modelo:** a qualidade das respostas varia conforme o modelo LLM escolhido (modelos menores podem ser menos precisos em português).
