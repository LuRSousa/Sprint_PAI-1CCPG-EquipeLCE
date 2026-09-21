**System prompt**

*v1 -> v2*

O que mudou:
- Adição de tags XML
- Regras de comportamento realocadas para a extremidade do system prompt
- Reforço de instrução para o modelo não criar infomações quando ele não possui dados suficientes
- Adição de comportamento para responder de forma afirmativa conforme as evidências e dados permitem

Por quê:
- Tornar a marcação de blocos do system prompt mais explícita, obrigando o modelo a passar por cada bloco 
- Reduzir a possibilidade de fenômeno "lost in middle"
- Evitar alucinação
- Evitar que modelo indique certeza mesmo em situações em os dados não são definitivos

Ganho medido:
- Tornou respostas mais completas 
- Respostas (textos e relatórios) mais sucintas
- Recomendações passo a passo mais objetivas

| Versão | O que mudou | Por que mudou | Ganho medido |
|---|---|---|---|
| V1 | Prompt estruturado em blocos de texto convencionais, sem tags XML. As regras de comportamento estavam posicionadas antes dos exemplos de interação e do comportamento em borda. Já havia instruções para não inventar informações e utilizar linguagem afirmativa, porém sem o refinamento explícito de adequar o grau de certeza às evidências disponíveis. | Estabelecer uma versão inicial funcional do system prompt, definindo identidade, contexto, dados disponíveis, regras de comportamento, exemplos de interação e comportamentos em situações de borda. | Servir como baseline para comparação com versões posteriores do system prompt. |
| V2 | Adição de tags XML para delimitar explicitamente os blocos do system prompt; realocação das regras de comportamento para a extremidade do prompt; reforço da instrução para não criar informações quando os dados disponíveis forem insuficientes; refinamento do comportamento de resposta afirmativa, condicionando o grau de certeza às evidências e aos dados disponíveis. | Tornar a marcação dos blocos do system prompt mais explícita; reduzir a possibilidade de efeitos associados ao fenômeno "lost in the middle"; reforçar as restrições contra alucinação; evitar que o modelo demonstre certeza em situações nas quais os dados não são definitivos. | As respostas tornaram-se mais completas; textos e relatórios apresentaram maior concisão; recomendações apresentadas passo a passo tornaram-se mais objetivas. Chatbot também apresentou comportamento mais alinhado às restrições.|

**Router system prompt**

*v1 -> v2*

| Versão | O que mudou | Por que mudou | Ganho medido |
|---|---|---|---|
| V1 | Prompt inicial com uma única instrução: classificar se o usuário está solicitando um relatório das sessões da semana corrente. Não havia definição explícita das categorias, exemplos de entradas, regras de decisão ou delimitação detalhada do escopo. | Estabelecer uma versão inicial simples do classificador, servindo como baseline para o versionamento e posterior evolução do system prompt. | Baixa acurácia de classificação do modelo provocada por perguntas que utilizavam "semana" como marco temporal ou que se referissem a sessões, fazendo-o classificar a entrada como "estruturada" incorretamente. |
| V2 | Estruturação do prompt com XML tagging (`<system_prompt>`, `<Identidade>`, `<Objetivo>`, `<estruturada>`, `<nao_estruturada>`, `<regras>`); definição explícita das duas categorias; inclusão dos campos pertencentes à saída estruturada; exemplos de perguntas estruturadas e não estruturadas; delimitação de que a análise estruturada se refere à semana corrente; criação de regras para priorizar a intenção da pergunta, tratar dúvidas como não estruturadas e impedir que o router responda à pergunta. | Reduzir ambiguidades da V1, orientar o modelo sobre os critérios objetivos de roteamento e diminuir classificações incorretas entre as chains estruturada e não estruturada. O XML tagging também atende ao requisito de context engineering e versionamento de system prompt do Sprint 03. | O modelo passou a classificar com maior acurácia a entrada do usuário. Palavras-chave, como "semana" e "sessões" não desviam equivocadamente a classificação do input para "estruturada" |