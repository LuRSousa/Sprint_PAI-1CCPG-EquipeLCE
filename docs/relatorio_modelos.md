# Relatório de modelos e parâmetros (Sprint 4)

Este relatório compara dois modelos no pipeline RAG final do ChargeGrid Assistant e justifica os parâmetros de geração e de busca: temperature, top_p, max_tokens e k. Todas as rodadas usam o mesmo eval set e o mesmo juiz do RAGAS; os números saem de `evals/resultados/comparativo_modelos.md` e `evals/resultados/teste_busca_k.md`. O relatório de modelos da Sprint 3, sem RAG, está em `docs/sprint3/relatorio_modelos.md`.

## 1. Como foi medido

- **Pipeline:** a iteração 4 do eval, que é a configuração do app: prompt RAG v2, busca intercalada (semântica + BM25) com a pergunta completada pela conversa e pelos dados, limiar 0,68 e embeddings `nomic-embed-text`. Detalhes em `docs/relatorio_rag.md`.
- **Eval set:** 24 itens, 19 que devem ser respondidos e 5 que devem ser recusados (`evals/eval_set_sprint4.json`).
- **O que muda entre as rodadas:** só o modelo que responde (`--modelo`), o limite de tokens de saída (`--max-tokens`) ou o número de trechos (`--k`). O router (`gpt-oss:120b`) e o juiz do RAGAS (`gpt-oss:120b`) são os mesmos em todas, para que a diferença venha do que está sendo comparado e não do juiz.
- **Métricas:** comportamento (respondeu ou recusou), fatos do gabarito, citação, citação certa, busca, faithfulness e answer relevancy do RAGAS, latência e tokens contados pelo próprio Ollama. Os dois modelos rodam no Ollama Cloud.

```powershell
python evals/avaliar.py --iteracao 4                                         # gpt-oss:120b, padrão do app
python evals/avaliar.py --iteracao 4 --modelo gpt-oss:20b                    # outro modelo
python evals/avaliar.py --iteracao 4 --modelo gpt-oss:20b --max-tokens 2048  # outro limite de saída
python evals/teste_busca_eval.py --varrer-k 2,3,4,6,8                        # k, sem LLM
```

## 2. Modelos comparados

| Modelo | Tamanho | Observação |
|---|---|---|
| `gpt-oss:120b` | ~117 bilhões de parâmetros, ~5,1 bilhões ativos por token (mistura de especialistas) | modelo do app desde a Sprint 3 |
| `gpt-oss:20b` | ~21 bilhões de parâmetros, ~3,6 bilhões ativos por token | o menor da mesma família |

Os dois são modelos abertos da OpenAI que raciocinam antes de responder. Esse raciocínio também é contado como token de saída, e isso pesa no max_tokens (seção 5).

## 3. Parâmetros

| Parâmetro | Valor | Por quê |
|---|---|---|
| temperature | 0 | Recomendação do enunciado. A resposta fica presa ao contexto e o eval é repetível entre iterações. A Sprint 3 usava 0,2, e o relatório dela mostrou que subir para 0,7 deixou as respostas mais variadas e mais lentas. |
| top_p | 0,9 | Mantido da Sprint 3. Com temperature 0, o modelo escolhe sempre o token mais provável, então o top_p (que corta a cauda das opções) praticamente não muda o resultado. |
| max_tokens (`num_predict`) | 1024 | A Sprint 3 usava 512 e, no eval, isso deu uma resposta vazia (base-07) e um relatório semanal cortado no meio. Na Sprint 4 as respostas trazem a citação de cada informação e ficaram mais longas: a maior do 120b usou 958 tokens. A seção 5 mostra o que acontece com o 20b. |
| k | 4 | O menor k que traz a seção certa em 15 de 16 perguntas (seção 6). |

## 4. gpt-oss:120b × gpt-oss:20b

Mesma iteração, mesmos parâmetros (temperature 0, top_p 0,9, max_tokens 1024, k 4):

| | `gpt-oss:120b` | `gpt-oss:20b` |
|---|---|---|
| Comportamento certo | 23/24 | 20/24 |
| … respondeu o que devia responder | 18/19 | 15/19 |
| … recusou o que devia recusar | 5/5 | 5/5 |
| Fatos do gabarito na resposta | 17/19 | 14/19 |
| Cita a fonte | 19/19 | 16/19 |
| Cita o documento e a seção certos | 17/19 | 14/19 |
| Busca trouxe uma seção esperada | 14/15 | 14/15 |
| RAGAS faithfulness | 0,97 (n = 19) | 0,93 (n = 16) |
| RAGAS answer relevancy | 0,81 | 0,71 |
| Latência por pergunta (média) | 5,1 s | 9,0 s |
| Tokens de saída por pergunta (média) | 436 | 513 |

O que os números mostram:

- **A busca é a mesma** (14/15 nos dois), porque o pipeline não muda; toda a diferença vem do modelo que escreve a resposta.
- **O 20b bateu no limite de saída em 4 das 19 respostas.** Três vieram vazias (base-11, dados-02 e misto-01): o modelo gastou o limite inteiro raciocinando e não chegou a escrever a resposta. A quarta (base-08, choque elétrico) foi cortada no meio do segundo passo, antes do SAMU 192 e dos Bombeiros 193. Nessas quatro, a contagem de tokens de saída passou de 1.024 (de 1.095 a 1.145, somando o router). Das 5 respostas que o 20b errou, 4 são esse corte; a quinta (base-06) é a mesma falha de busca do 120b.
- **A faithfulness do 20b parece melhor do que é:** as 3 respostas vazias não têm afirmações para conferir e ficam fora da média (n = 16). A answer relevancy pune essas respostas com 0, e por isso cai para 0,71.
- **O modelo menor não foi mais rápido.** No Ollama Cloud, o 20b levou quase o dobro do tempo, porque escreveu mais tokens (raciocínio incluído) e a resposta mais lenta levou 16,7 s, contra 10,3 s da mais lenta do 120b. Para o operador, isso é espera sem ganho.
- **Onde o 20b foi melhor:** na dados-01 ele listou a potência de cada carregador ativo, que o gabarito pede e o 120b omitiu.

## 5. max_tokens: quanto o modelo pode escrever

O gpt-oss raciocina antes de responder, e esse raciocínio conta no `num_predict`. Se o limite acaba durante o raciocínio, a resposta volta vazia; se acaba durante a resposta, ela volta cortada. Para saber se as 4 falhas do 20b eram só o limite, a mesma rodada foi repetida com `--max-tokens 2048`:

| | `gpt-oss:120b` · 1024 | `gpt-oss:20b` · 1024 | `gpt-oss:20b` · 2048 |
|---|---|---|---|
| Comportamento certo | 23/24 | 20/24 | 23/24 |
| Fatos do gabarito na resposta | 17/19 | 14/19 | 16/19 |
| Cita a fonte | 19/19 | 16/19 | 18/19 |
| Cita o documento e a seção certos | 17/19 | 14/19 | 16/19 |
| RAGAS faithfulness | 0,97 (n = 19) | 0,93 (n = 16) | 0,93 (n = 18) |
| RAGAS answer relevancy | 0,81 | 0,71 | 0,79 |
| Respostas que bateram no limite | 0 | 4 (3 vazias, 1 cortada) | 1 (vazia) |
| Latência média | 5,1 s | 9,0 s | 11,0 s |
| Pergunta mais lenta | 10,3 s | 16,7 s | 31,4 s |
| Tokens de saída por pergunta (média) | 436 | 513 | 545 |

As perguntas que mudaram de uma rodada do 20b para a outra (tokens de saída somando o router):

| Pergunta | 20b · 1024 | 20b · 2048 |
|---|---|---|
| base-07: deixar o carro carregando a noite toda no condomínio | 570 tokens, certa | 2.133 tokens, vazia (31,4 s) |
| base-08: choque elétrico no carregador | 1.101 tokens, cortada antes do 192/193 | 732 tokens, certa |
| base-11: recarga interrompida por falha, o cliente paga? | 1.145 tokens, vazia | 702 tokens, certa |
| dados-02: faturamento do mês | 1.095 tokens, vazia | 495 tokens, certa |
| misto-01: alerta do carregador 3 | 1.121 tokens, vazia | 1.246 tokens, certa |
| misto-02: cobrança da SESS-004 | 933 tokens, certa | 1.158 tokens, certa |

O que os números mostram:

- **Com 2048, as 4 falhas da rodada com 1024 viraram respostas certas**, e a base-08 chegou ao SAMU 192 e aos Bombeiros 193. O comportamento subiu de 20/24 para 23/24 e a answer relevancy, de 0,71 para 0,79.
- **O que mais mudou foi o tamanho do raciocínio, não só o limite.** Três das quatro usaram bem menos de 1.024 tokens desta vez; só a misto-01 passou disso. A misto-02, que tinha cabido em 1024, usou 1.158. E a base-07, respondida com 570 tokens na primeira rodada, raciocinou até o novo limite e voltou vazia depois de 31 s. Mesmo com temperature 0, o Ollama Cloud não devolve sempre a mesma saída, e no 20b o que mais varia é quanto ele raciocina.
- **O 23/24 empata com o 120b só no comportamento.** A base-06 conta como respondida porque o 20b escreveu "o documento não especifica um tempo máximo de reserva" em vez da frase de recusa, mas o fato do gabarito (4 horas) continua faltando, pela mesma falha de busca. A dados-01 perdeu a potência dos carregadores, que tinha trazido com 1024. Em fatos, citação certa, faithfulness e answer relevancy, o 20b continua atrás.
- **Mais limite é mais espera:** a latência média foi a 11,0 s, mais que o dobro da do 120b, e a pergunta mais lenta levou 31,4 s.

**Decisão: o app fica com 1024.** No 120b, nenhuma resposta bateu no limite, mas a maior (base-01, o procedimento de falha de comunicação) usou 958 tokens, então a folga é pequena. O limite é um teto: subir para 2048 não deixa mais lentas as respostas que terminam antes; só deixa terminar as que seriam cortadas, e aumenta a espera quando o raciocínio se estende. Se aparecerem respostas cortadas no uso, o próximo passo é 2048 no 120b, medido antes com `python evals/avaliar.py --iteracao 4 --max-tokens 2048`. No 20b, dobrar o limite trocou 4 falhas por 1 e por mais espera: o raciocínio dele varia demais para um limite fixo resolver.

## 6. k: quantos trechos levar para o prompt

O `teste_busca_eval.py --varrer-k` mede, sem LLM, em quantas das 16 perguntas com seção esperada a busca do app (intercalada, com a pergunta completada) traz essa seção, e quanto texto vai para o prompt:

| k | Perguntas com a seção esperada | Trechos por pergunta (média) | Caracteres de trecho por pergunta (média) | Trechos nas perguntas fora do domínio |
|---|---|---|---|---|
| 2 | 13/16 | 2,0 | 679 | 0 e 0 |
| 3 | 13/16 | 3,0 | 1.067 | 0 e 0 |
| **4** | **15/16** | **4,0** | **1.409** | **0 e 0** |
| 6 | 15/16 | 5,8 | 1.981 | 0 e 0 |
| 8 | 16/16 | 7,4 | 2.491 | 0 e 0 |

- **k = 4 é o menor k que chega a 15/16.** Com 2 ou 3 trechos, a busca perde o choque elétrico (base-08) e o percentual de potência (dados-03).
- **k = 6 não acerta nenhuma pergunta a mais** e leva 40% mais texto para o prompt.
- **k = 8 recupera a base-06** (a reserva de 4 horas no condomínio, que a pergunta chama de "tempo" e o texto de "duração"), ao custo de 77% mais texto de trecho em toda pergunta: perto de 1.080 caracteres, uns 270 tokens a mais, mesmo nas perguntas que já acertavam com 4.
- Em todos os valores, as perguntas fora do domínio continuam sem nenhum trecho, então o guardrail de escopo não é afetado.

O eval completo com k = 8 (com o modelo respondendo e o RAGAS) ficou para o próximo ciclo. Ele mostraria se a base-06 recuperada vira resposta certa e se os trechos a mais mudam a faithfulness e a latência; o comando é `python evals/avaliar.py --iteracao 4 --k 8`. Com o que foi medido, k = 4 continua o padrão: o ganho de k = 8 é 1 pergunta em 16, e o custo vale para todas.

## 7. Conclusão

O app continua com `gpt-oss:120b`, temperature 0, top_p 0,9, max_tokens 1024 e k 4.

- **Modelo:** o 120b ficou à frente do 20b nas duas rodadas em fatos, citação, faithfulness e answer relevancy, com cerca de metade da espera. O 20b só empatou no comportamento com o dobro do limite de saída e, mesmo assim, com 11 s de espera média. Para o operador, que pergunta no meio do atendimento, o modelo maior é o mais rápido e o mais confiável.
- **Parâmetros:** temperature 0 e top_p 0,9 ficam como estão (seção 3); 1024 tokens bastam para o 120b neste eval set, com pouca folga (seção 5); k = 4 é o menor k que traz a seção certa em 15 de 16 perguntas (seção 6).
- **Limite das medidas:** cada rodada é uma amostra. Mesmo com temperature 0, o Ollama Cloud devolve saídas diferentes entre rodadas: a base-07 do 20b usou 570 tokens numa e 2.133 na outra, e a dados-01 trouxe a potência numa e não na outra. Diferença de uma pergunta entre duas colunas está dentro dessa variação; as conclusões acima se apoiam em diferenças que aparecem em várias perguntas e em várias métricas ao mesmo tempo.
- **Próximos testes:** repetir cada configuração 2 ou 3 vezes para medir a variação, rodar o 120b com `--max-tokens 2048` e o k = 8 de ponta a ponta.
