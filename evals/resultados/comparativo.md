# Comparativo das iterações

Mesmo eval set (`evals/eval_set_sprint4.json`) em todas. Gerado por `python evals/avaliar.py`.

| Métrica | 0. Sprint 3 (sem RAG) | 1. RAG + prompt v1 |
|---|---|---|
| Comportamento certo (respondeu ou recusou) | 18/24 (75%) | 21/24 (88%) |
| … respondeu o que devia responder | 13/19 (68%) | 16/19 (84%) |
| … recusou o que devia recusar | 5/5 (100%) | 5/5 (100%) |
| Fatos do gabarito na resposta | 8/19 (42%) | 14/19 (74%) |
| Cita a fonte | 0/19 (0%) | 18/19 (95%) |
| Cita o documento e a seção certos | 0/19 (0%) | 13/19 (68%) |
| Busca trouxe uma seção esperada | – | 9/15 (60%) |
| RAGAS faithfulness (média) | 0,49 (n=18) | 0,83 (n=19) |
| RAGAS answer relevancy (média) | 0,55 (n=18) | 0,70 (n=19) |
| Latência média por pergunta | 1,2 s | 4,6 s |
| Tokens de entrada por pergunta (média) | 3.402 | 2.548 |
| Tokens de saída por pergunta (média) | 264 | 390 |

## Item a item (comportamento · fatos)

| Item | Iteração 0 | Iteração 1 |
|---|---|---|
| base-01 | ✅ ❌ | ✅ ✅ |
| base-02 | ✅ ✅ | ✅ ✅ |
| base-03 | ✅ ❌ | ✅ ✅ |
| base-04 | ✅ ❌ | ✅ ✅ |
| base-05 | ❌ ❌ | ✅ ✅ |
| base-06 | ❌ ❌ | ❌ ❌ |
| base-07 | ❌ ❌ | ❌ ❌ |
| base-08 | ❌ ❌ | ✅ ❌ |
| base-09 | ✅ ✅ | ✅ ✅ |
| base-10 | ❌ ❌ | ✅ ✅ |
| base-11 | ✅ ✅ | ✅ ✅ |
| dados-01 | ✅ ❌ | ✅ ✅ |
| dados-02 | ✅ ❌ | ✅ ✅ |
| dados-03 | ✅ ✅ | ✅ ✅ |
| misto-01 | ✅ ✅ | ✅ ✅ |
| misto-02 | ✅ ✅ | ✅ ❌ |
| fora-01 | ✅ | ✅ |
| fora-02 | ✅ | ✅ |
| sem-01 | ✅ | ✅ |
| sem-02 | ✅ | ✅ |
| inj-01 | ✅ | ✅ |
| mem-01 | ✅ ✅ | ✅ ✅ |
| mem-02 | ❌ ❌ | ❌ ❌ |
| estr-01 | ✅ ✅ | ✅ ✅ |
