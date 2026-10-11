# Busca: qualidade do contexto recuperado

- Data: 10/10/2026 22:10 · coleção `chargegrid_kb` · k = 4 · limiar 0.68
- Célula: posição da primeira seção esperada entre os trechos que vão para o prompt (– = nenhuma).

| Item | Seções esperadas | vetorial | bm25 | híbrida | vetorial + consulta | híbrida + consulta | ... BM25 peso 2 |
|---|---|---|---|---|---|---|---|
| base-01 | 01 §5.1, 06 §2.1 | 1º | 2º | 1º | 1º | 1º | 1º |
| base-02 | 02 §3, 02 §2 | 1º | 2º | 1º | 1º | 1º | 1º |
| base-03 | 04 §2, 06 §1.5 | 1º | 1º | 1º | 1º | 1º | 1º |
| base-04 | 04 §5, 06 §1.6 | 1º | 1º | 1º | 1º | 1º | 1º |
| base-05 | 02 §6, 06 §1.2 | 1º | 1º | 1º | 1º | 1º | 1º |
| base-06 | 05 §4.1 | – | – | – | – | – | – |
| base-07 | 05 §4.2, 05 §4.1 | – | 1º | – | – | – | – |
| base-08 | 07 §4.3 | – | 2º | – | – | – | – |
| base-09 | 03 §6.2 | 1º | 2º | 1º | 1º | 1º | 1º |
| base-10 | 01 §6.2, 06 §2.2, 03 §8 | 1º | 2º | 2º | 1º | 2º | 2º |
| base-11 | 04 §6, 06 §1.7 | 1º | 1º | 1º | 1º | 1º | 1º |
| dados-03 | 01 §4.2, 01 §5.3 | 3º | 2º | 2º | 3º | 2º | 2º |
| misto-01 | 01 §5.2 | – | – | – | 2º | 1º | 1º |
| misto-02 | 04 §3, 04 §4, 04 §2 | – | – | – | 2º | 2º | 1º |
| sem-02 | 04 §7 | 1º | 1º | 1º | 1º | 1º | 1º |
| mem-02 | 04 §2, 06 §1.5 | – | – | – | 2º | 1º | 1º |
| **Acertos** | | **10/16** | **12/16** | **10/16** | **13/16** | **13/16** | **13/16** |

## Perguntas fora do domínio (trechos que passariam para o prompt)

| Item | Pergunta | vetorial | bm25 | híbrida | vetorial + consulta | híbrida + consulta | ... BM25 peso 2 |
|---|---|---|---|---|---|---|---|
| fora-01 | Qual é a capital da Austrália? | 0 | 0 | 0 | 0 | 0 | 0 |
| fora-02 | Me indica um bom filme para assistir hoje à noite? | 0 | 0 | 0 | 0 | 0 | 0 |
