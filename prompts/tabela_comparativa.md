**System prompt**

*v1 -> v2*

O que mudou:
- Adição de tags XML
- Regras de comportamento realocadas para a extremidade do system prompt
- Adição de instrução direta para o modelo não criar infomações quando ele não possui dados suficientes
- Adição de comportamento para responder de forma afirmativa conforme as evidências e dados permitem
- Remoção de exemplo de resposta que inclui projeções para fechamento do mês

Por quê:
- Tornar a marcação de blocos do system prompt mais explícita, obrigando o modelo a passar por cada bloco 
- Evitar fenômeno "lost in middle"
- Evitar alucinação
- Evitar que modelo indique certeza mesmo em situações em os dados não são definitivos
- Manter consistência com a instrução de não inventar informações, uma vez que os dados disponíveis não permitem fazer essas projeções

Ganho medido:

**Router system prompt**

*v1 -> v2*

| Versão | O que mudou | Por que mudou | Ganho medido |
|---|---|---|---|
| V1 | Prompt inicial com uma única instrução: classificar se o usuário está solicitando um relatório das sessões da semana corrente. Não havia definição explícita das categorias, exemplos de entradas, regras de decisão ou delimitação detalhada do escopo. | Estabelecer uma versão inicial simples do classificador, servindo como baseline para o versionamento e posterior evolução do system prompt. | Baixa acurácia de classificação do modelo provocada por perguntas que utilizavam "semana" como marco temporal ou que se referissem a sessões, fazendo-o classificar a entrada como "estruturada" incorretamente. |
| V2 | Estruturação do prompt com XML tagging (`<system_prompt>`, `<Identidade>`, `<Objetivo>`, `<estruturada>`, `<nao_estruturada>`, `<regras>`); definição explícita das duas categorias; inclusão dos campos pertencentes à saída estruturada; exemplos de perguntas estruturadas e não estruturadas; delimitação de que a análise estruturada se refere à semana corrente; criação de regras para priorizar a intenção da pergunta, tratar dúvidas como não estruturadas e impedir que o router responda à pergunta. | Reduzir ambiguidades da V1, orientar o modelo sobre os critérios objetivos de roteamento e diminuir classificações incorretas entre as chains estruturada e não estruturada. O XML tagging também atende ao requisito de context engineering e versionamento de system prompt do Sprint 03. | O modelo passou a classificar com maior acurácia a entrada do usuário. Palavras-chave, como "semana" e "sessões" não desviam equivocadamente a classificação do input para "estruturada" |