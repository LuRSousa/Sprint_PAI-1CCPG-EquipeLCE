# Avaliação do ChargeGrid Assistant (Sprint 4)

O mesmo conjunto de perguntas roda em cada versão do assistente, e as notas mostram o que melhorou de uma iteração para a outra.

## Eval set

`eval_set_sprint4.json` tem 24 itens: 11 sobre a base de conhecimento, 3 sobre os dados operacionais, 2 que juntam dados e base, 2 fora do escopo, 2 que pedem informação que a base não tem, 1 injeção na pergunta, 2 conversas de dois turnos (memória) e 1 relatório semanal (chain estruturada).

Cada item traz:

| Campo | Para que serve |
|---|---|
| `turnos` | a pergunta, ou as perguntas da conversa, na ordem |
| `esperado` | `responder` ou `recusar` |
| `fontes_esperadas` | as seções da base que respondem (`["04", "5"]` = arquivo 04, seção 5) |
| `deve_conter` | fatos que a resposta precisa trazer; cada posição é uma lista de jeitos de dizer a mesma coisa |
| `nao_deve_conter` | o que a resposta não pode dizer (número errado, informação que veio de injeção) |
| `referencia` | a resposta do gabarito, escrita a partir dos PDFs e do `data/mock_data.json` |

## Como rodar

Na raiz do projeto, com o venv ativo, o `.env` preenchido e o Ollama aberto:

```powershell
python evals/avaliar.py --iteracao 1 --amostra 3   # teste rápido com 3 perguntas
python evals/avaliar.py --iteracao 0               # Sprint 3, sem RAG
python evals/avaliar.py --iteracao 1               # RAG + prompt v1
python evals/avaliar.py --iteracao 2               # RAG + prompt v2
```

| Opção | O que faz |
|---|---|
| `--amostra N` | roda só N itens, começando por um de cada categoria |
| `--ids base-01,fora-01` | roda só esses itens |
| `--sem-ragas` | só as verificações automáticas, sem chamar o juiz |
| `--continuar` | retoma de onde parou (erro, Ctrl+C ou limite de uso do Ollama Cloud) |
| `--comparativo` | só refaz o `comparativo.md` (e o `comparativo_modelos.md`) com as rodadas já feitas |
| `--reverificar` | refaz só as verificações automáticas com as respostas já salvas, sem chamar modelo (para quando o verificador melhora) |
| `--modelo gpt-oss:20b` | troca o modelo que responde, para o `relatorio_modelos.md`; o router e o juiz continuam os mesmos |

Uma iteração completa faz perto de 150 chamadas ao Ollama Cloud: umas 50 do assistente (router e resposta) e umas 95 do juiz (5 por resposta avaliada). Se o Ollama Cloud recusar por limite de uso, o eval para, guarda o que já fez e mostra o comando para continuar depois.

## O que é medido

Em todos os itens, sem LLM:

- **Comportamento:** respondeu o que devia responder e recusou o que devia recusar.
- **Fatos:** a resposta traz o que está em `deve_conter` e nada do `nao_deve_conter`.
- **Cita a fonte:** a resposta tem `(Fonte: ...)`.
- **Citação certa:** a citação aponta um documento e uma seção de `fontes_esperadas` (ou os dados operacionais, quando a resposta vem só deles).
- **Busca:** algum dos trechos recuperados é de uma seção esperada (só nas iterações com RAG).
- **Latência e tokens** da pergunta, com os tokens contados pelo próprio Ollama.

Com o RAGAS, nos itens que devem ser respondidos:

- **Faithfulness:** o juiz quebra a resposta em afirmações e confere cada uma no contexto que o modelo recebeu (trechos da base e dados do posto). 1 = tudo sustentado pelo contexto.
- **Answer relevancy:** o juiz escreve 3 perguntas que a resposta responderia, e o embedding compara cada uma com a pergunta original. Resposta evasiva ("não encontrei") recebe 0.

## Detalhes do RAGAS neste projeto

- Versão fixada: `ragas==0.4.3`, com a API clássica (`ragas.metrics` + `LangchainLLMWrapper`), que aceita o `ChatOllama`. A API nova (`ragas.metrics.collections`) só aceita cliente no formato da OpenAI.
- O ragas pede o `scikit-network`, que ele só usa para gerar testsets (o projeto não usa). As versões novas não têm instalador pronto para Python 3.14 no Windows e pedem o compilador C++, então o `requirements.txt` fixa a 0.12.1, que é só Python.
- O `ragas_compat.py` cria um módulo vazio para `langchain_community.chat_models.vertexai`, que o ragas 0.4.3 importa e o langchain-community 0.4 não tem mais. Sem isso, `import ragas` quebra.
- **Juiz:** `gpt-oss:120b` no Ollama Cloud, fixo (não muda quando o `--modelo` troca o assistente, senão a nota mediria o juiz junto), com raciocínio "low" e uma chamada por vez. Dá para trocar com `RAGAS_JUIZ` no `.env`.
- **Afirmações sem apoio:** além da nota, o eval guarda cada afirmação que o juiz considerou sem apoio no contexto, com o motivo. Elas aparecem no `.md` de cada iteração e servem de evidência no relatório. O juiz também erra (às vezes marca como sem apoio uma frase que está no trecho), por isso as notas são lidas junto com as respostas.
- **Idioma:** os prompts do RAGAS são em inglês; foi acrescentado o pedido de escrever no idioma da resposta. Sem isso, as perguntas da answer relevancy saem em inglês e a comparação com a pergunta em português fica injusta.
- **Embedding:** o mesmo `nomic-embed-text` do RAG, com o prefixo de consulta dos dois lados (pergunta contra pergunta). Como esse modelo foi treinado mais em inglês, o valor absoluto da answer relevancy fica mais baixo do que seria com um embedding multilíngue; a comparação entre iterações continua valendo, porque todas usam o mesmo.
- O verificador automático normaliza o texto antes de comparar com o gabarito: tira acento e o negrito do markdown e junta números com separador de milhar ("R$ 6 248,00" com espaço fino vira 6248). Resposta vazia conta como não respondida.

## Arquivos

| Arquivo | O que tem |
|---|---|
| `avaliar.py` | roda o eval set numa iteração e escreve os resultados |
| `sprint3_baseline.py` | o assistente como estava na Sprint 3 (iteração 0) |
| `ragas_compat.py` | ligação do RAGAS com o Ollama e com o embedding do RAG |
| `resultados/iteracao_<n>.json` | tudo, item a item: resposta, trechos, verificações e notas |
| `resultados/iteracao_<n>.md` | resumo, tabela item a item e as respostas |
| `resultados/comparativo.md` | as iterações completas lado a lado |
| `teste_busca.py`, `teste_seguranca.py`, `perguntar.py` | testes dos blocos anteriores (busca, segurança, pergunta avulsa) |
