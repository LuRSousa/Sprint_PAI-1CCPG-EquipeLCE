# Busca: quantos trechos levar para o prompt (k)

- Data: 14/10/2026 15:33 · coleção `chargegrid_kb` · limiar 0.68 · k em uso: 4
- Acertos: perguntas (de 16) em que uma seção esperada está entre os trechos que vão para o prompt.

| k | vetorial | bm25 | híbrida | vetorial + consulta | híbrida + consulta | intercalada + consulta |
|---|---|---|---|---|---|---|
| 2 | 9/16 | 12/16 | 10/16 | 12/16 | 13/16 | 13/16 |
| 3 | 10/16 | 12/16 | 10/16 | 13/16 | 13/16 | 13/16 |
| 4 | 10/16 | 12/16 | 10/16 | 13/16 | 13/16 | 15/16 |
| 6 | 10/16 | 13/16 | 11/16 | 13/16 | 14/16 | 15/16 |
| 8 | 10/16 | 14/16 | 12/16 | 13/16 | 15/16 | 16/16 |

## Na busca do app (intercalada + consulta)

| k | Acertos | Trechos por pergunta (média) | Caracteres de trecho por pergunta (média) | Trechos nas perguntas fora do domínio | Perguntas sem seção esperada |
|---|---|---|---|---|---|
| 2 | 13/16 | 2,0 | 679 | 0 e 0 | base-06, base-08, dados-03 |
| 3 | 13/16 | 3,0 | 1.067 | 0 e 0 | base-06, base-08, dados-03 |
| 4 | 15/16 | 4,0 | 1.409 | 0 e 0 | base-06 |
| 6 | 15/16 | 5,8 | 1.981 | 0 e 0 | base-06 |
| 8 | 16/16 | 7,4 | 2.491 | 0 e 0 | – |

Cada caractere a mais de trecho também é token de entrada a mais em toda pergunta (em português, algo perto de 4 caracteres por token).
