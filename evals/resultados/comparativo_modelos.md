# Comparativo de modelos e parâmetros

Mesma iteração e mesmo eval set, trocando o modelo que responde (`--modelo`) ou o número de trechos no prompt (`--k`). O router e o juiz do RAGAS são os mesmos em todas as colunas.

## Iteração 4: RAG + prompt v2 + busca intercalada

| | `gpt-oss:120b` · max_tokens = 1024 | `gpt-oss:20b` · max_tokens = 1024 | `gpt-oss:20b` · max_tokens = 2048 |
|---|---|---|---|
| temperature | 0 | 0 | 0 |
| top_p | 0,9 | 0,9 | 0,9 |
| max_tokens (num_predict) | 1024 | 1024 | 2048 |
| k (trechos) | 4 | 4 | 4 |
| Comportamento certo (respondeu ou recusou) | 23/24 (96%) | 20/24 (83%) | 23/24 (96%) |
| … respondeu o que devia responder | 18/19 (95%) | 15/19 (79%) | 18/19 (95%) |
| … recusou o que devia recusar | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| Fatos do gabarito na resposta | 17/19 (89%) | 14/19 (74%) | 16/19 (84%) |
| Cita a fonte | 19/19 (100%) | 16/19 (84%) | 18/19 (95%) |
| Cita o documento e a seção certos | 17/19 (89%) | 14/19 (74%) | 16/19 (84%) |
| Busca trouxe uma seção esperada | 14/15 (93%) | 14/15 (93%) | 14/15 (93%) |
| RAGAS faithfulness (média) | 0,97 (n=19) | 0,93 (n=16) | 0,93 (n=18) |
| … só das respostas dadas (sem as recusas) | 0,97 (n=18) | 0,95 (n=15) | 0,93 (n=18) |
| RAGAS answer relevancy (média) | 0,81 (n=19) | 0,71 (n=19) | 0,79 (n=19) |
| Latência média por pergunta | 5,1 s | 9,0 s | 11,0 s |
| Tokens de entrada por pergunta (média) | 2.944 | 2.940 | 2.939 |
| Tokens de saída por pergunta (média) | 436 | 513 | 545 |

