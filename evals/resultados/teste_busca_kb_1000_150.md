# Teste de busca: coleção `kb_1000_150`

- Data: 09/10/2026 14:13
- Chunks na coleção: 100 | chunk_size: 1000 | overlap: 150 | k: 5

## Perguntas que a base responde

| # | Pergunta | Nota do 1º | Seção esperada no 1º? | No top-k? |
|---|---|---|---|---|
| 1 | O carregador 2 está offline. O que o operador deve fazer? | 0.773 | sim | sim |
| 2 | Quanto custa recarregar às 18h? | 0.697 | sim | sim |
| 3 | Qual é a potência máxima do carregador 3? | 0.759 | não | sim |
| 4 | Posso deixar o carro conectado a noite toda na garagem do condomínio? | 0.700 | não | NÃO |
| 5 | Por que a recarga fica mais lenta perto de 80%? | 0.842 | sim | sim |
| 6 | Como é calculada a projeção de faturamento do mês? | 0.702 | sim | sim |
| 7 | O que fazer se sair fumaça do carregador? | 0.725 | sim | sim |
| 8 | Meu carro usa conector CHAdeMO. Consigo carregar no posto? | 0.757 | sim | sim |
| 9 | O que é a taxa de ociosidade e quanto custa? | 0.758 | sim | sim |
| 10 | Qual o melhor horário para fazer manutenção nos carregadores? | 0.805 | sim | sim |
| 11 | O assistente consegue reiniciar um carregador? | 0.771 | sim | sim |
| 12 | A sessão foi interrompida por falha do carregador. O cliente paga? | 0.747 | sim | sim |

## Fora do domínio

| Pergunta | Nota do 1º | 1º trecho |
|---|---|---|
| Qual é a capital da Austrália? | 0.650 | 05 Regimento modelo de recarga compartilhada em condomínio | 4.3 Uso sem reserva | p. 1 |
| Me passa uma receita de bolo de chocolate. | 0.663 | 03 Guia da plataforma EV ChargeOps | 6.2 Como os indicadores são calculados | p. 2 |
| Quem ganhou a Copa do Mundo de 2022? | 0.612 | 06 Perguntas frequentes sobre recarga | 1.2 Meu carro é compatível com o posto? | p. 1 |

## Do domínio, sem resposta na base

| Pergunta | Nota do 1º | 1º trecho |
|---|---|---|
| Qual é o peso do carregador? | 0.742 | 06 Perguntas frequentes sobre recarga | 2.2 Posso aumentar o limite de potência de um carregador? | p. 2 |
| Qual é a bandeira tarifária deste mês? | 0.768 | 04 Tabela tarifária do posto | 7 Adicional de bandeira tarifária | p. 2 |

## Resumo

- Seção certa no 1º trecho: 10/12
- Seção certa entre os 5 primeiros: 11/12
- Menor nota do 1º trecho nas perguntas da base: 0.697
- Maior nota do 1º trecho fora do domínio: 0.663
- Notas do 1º trecho sem resposta na base: 0.742, 0.768
- Limiar: as notas separam bem: um limiar entre 0.66 e 0.70 (ex.: 0.68) recusa o que está fora do domínio

## Trechos devolvidos

**1. O carregador 2 está offline. O que o operador deve fazer?**
- 0.773 · 06 Perguntas frequentes sobre recarga | 2.1 Um carregador aparece offline. O que faço primeiro? | p. 2
- 0.766 · 01 Manual do Operador ChargeGrid | 5.1 Falha de comunicação (falha_comunicacao, crítico) | p. 3
- 0.757 · 01 Manual do Operador ChargeGrid | 5.1 Falha de comunicação (falha_comunicacao, crítico) | p. 3
- 0.743 · 01 Manual do Operador ChargeGrid | 4.2 Tipos de alerta | p. 2
- 0.743 · 07 Segurança e emergência no eletroposto | 2.2 O operador não pode | p. 1

**2. Quanto custa recarregar às 18h?**
- 0.697 · 06 Perguntas frequentes sobre recarga | 1.5 Quanto custa recarregar? | p. 1
- 0.682 · 06 Perguntas frequentes sobre recarga | 2.3 Qual o melhor horário para fazer manutenção? | p. 2
- 0.670 · 06 Perguntas frequentes sobre recarga | 2.6 O que faço quando um motorista deixa o carro parado depois da recarga? | p. 2
- 0.661 · 06 Perguntas frequentes sobre recarga | 1.6 O que é a taxa de ociosidade? | p. 1
- 0.659 · 06 Perguntas frequentes sobre recarga | 1.8 Posso recarregar na chuva? | p. 1

**3. Qual é a potência máxima do carregador 3?**
- 0.759 · 02 Especificações técnicas dos carregadores do posto | 5 Potência real da recarga | p. 2
- 0.751 · 02 Especificações técnicas dos carregadores do posto | 3 Unidades instaladas | p. 2
- 0.749 · 01 Manual do Operador ChargeGrid | 3.2 Potência e percentual de uso | p. 2
- 0.747 · 06 Perguntas frequentes sobre recarga | 2.2 Posso aumentar o limite de potência de um carregador? | p. 2
- 0.740 · 01 Manual do Operador ChargeGrid | 5.3 Potência próxima do limite (potencia_proxima_limite, aviso) | p. 3

**4. Posso deixar o carro conectado a noite toda na garagem do condomínio?**
- 0.700 · 05 Regimento modelo de recarga compartilhada em condomínio | 2 Definições | p. 1
- 0.695 · 05 Regimento modelo de recarga compartilhada em condomínio | 1 Objetivo e abrangência | p. 1
- 0.682 · 05 Regimento modelo de recarga compartilhada em condomínio | 3.1 Cadastro | p. 1
- 0.682 · 06 Perguntas frequentes sobre recarga | 2.6 O que faço quando um motorista deixa o carro parado depois da recarga? | p. 2
- 0.668 · 05 Regimento modelo de recarga compartilhada em condomínio | 5.1 Energia | p. 2

**5. Por que a recarga fica mais lenta perto de 80%?**
- 0.842 · 06 Perguntas frequentes sobre recarga | 1.3 Por que a recarga fica mais lenta perto de 80%? | p. 1
- 0.693 · 06 Perguntas frequentes sobre recarga | 1.4 Quanto tempo leva uma recarga? | p. 1
- 0.691 · 06 Perguntas frequentes sobre recarga | 1.6 O que é a taxa de ociosidade? | p. 1
- 0.685 · 06 Perguntas frequentes sobre recarga | 1.5 Quanto custa recarregar? | p. 1
- 0.679 · 06 Perguntas frequentes sobre recarga | 1.7 A recarga parou no meio. Vou pagar? | p. 1

**6. Como é calculada a projeção de faturamento do mês?**
- 0.702 · 03 Guia da plataforma EV ChargeOps | 6.2 Como os indicadores são calculados | p. 2
- 0.692 · 06 Perguntas frequentes sobre recarga | 2.4 Onde vejo o faturamento do mês? | p. 2
- 0.689 · 04 Tabela tarifária do posto | 4 Exemplos de cálculo | p. 1
- 0.687 · 04 Tabela tarifária do posto | 3 Regra de aplicação da faixa | p. 1
- 0.674 · 03 Guia da plataforma EV ChargeOps | 6.1 Indicadores do mês | p. 2

**7. O que fazer se sair fumaça do carregador?**
- 0.725 · 07 Segurança e emergência no eletroposto | 4.1 Fumaça, cheiro de queimado ou fogo no carregador | p. 1
- 0.706 · 07 Segurança e emergência no eletroposto | 4.6 Colisão contra o carregador | p. 2
- 0.699 · 04 Tabela tarifária do posto | 6 Sessões interrompidas por falha | p. 1
- 0.685 · 07 Segurança e emergência no eletroposto | 4.5 Alagamento | p. 2
- 0.677 · 01 Manual do Operador ChargeGrid | 4.2 Tipos de alerta | p. 2

**8. Meu carro usa conector CHAdeMO. Consigo carregar no posto?**
- 0.757 · 02 Especificações técnicas dos carregadores do posto | 6 Compatibilidade com veículos | p. 2
- 0.757 · 06 Perguntas frequentes sobre recarga | 1.2 Meu carro é compatível com o posto? | p. 1
- 0.721 · 04 Tabela tarifária do posto | 6 Sessões interrompidas por falha | p. 1
- 0.714 · 06 Perguntas frequentes sobre recarga | 1.8 Posso recarregar na chuva? | p. 1
- 0.711 · 07 Segurança e emergência no eletroposto | 4.6 Colisão contra o carregador | p. 2

**9. O que é a taxa de ociosidade e quanto custa?**
- 0.758 · 06 Perguntas frequentes sobre recarga | 1.6 O que é a taxa de ociosidade? | p. 1
- 0.756 · 04 Tabela tarifária do posto | 5 Taxa de ociosidade | p. 1
- 0.684 · 06 Perguntas frequentes sobre recarga | 2.6 O que faço quando um motorista deixa o carro parado depois da recarga? | p. 2
- 0.653 · 03 Guia da plataforma EV ChargeOps | 7 Relatório semanal de demanda | p. 3
- 0.647 · 03 Guia da plataforma EV ChargeOps | 4.1 Status das sessões | p. 1

**10. Qual o melhor horário para fazer manutenção nos carregadores?**
- 0.805 · 06 Perguntas frequentes sobre recarga | 2.3 Qual o melhor horário para fazer manutenção? | p. 2
- 0.762 · 01 Manual do Operador ChargeGrid | 7.3 Melhor horário para manutenção | p. 5
- 0.708 · 03 Guia da plataforma EV ChargeOps | 7 Relatório semanal de demanda | p. 3
- 0.691 · 07 Segurança e emergência no eletroposto | 4.5 Alagamento | p. 2
- 0.687 · 06 Perguntas frequentes sobre recarga | 1.8 Posso recarregar na chuva? | p. 1

**11. O assistente consegue reiniciar um carregador?**
- 0.771 · 06 Perguntas frequentes sobre recarga | 2.5 O ChargeGrid Assistant pode ligar, desligar ou reiniciar carregadores? | p. 2
- 0.705 · 07 Segurança e emergência no eletroposto | 4.5 Alagamento | p. 2
- 0.703 · 01 Manual do Operador ChargeGrid | 5.1 Falha de comunicação (falha_comunicacao, crítico) | p. 3
- 0.701 · 07 Segurança e emergência no eletroposto | 4.6 Colisão contra o carregador | p. 2
- 0.699 · 07 Segurança e emergência no eletroposto | 2.1 O operador pode | p. 1

**12. A sessão foi interrompida por falha do carregador. O cliente paga?**
- 0.747 · 04 Tabela tarifária do posto | 6 Sessões interrompidas por falha | p. 1
- 0.746 · 06 Perguntas frequentes sobre recarga | 1.7 A recarga parou no meio. Vou pagar? | p. 1
- 0.692 · 07 Segurança e emergência no eletroposto | 4.6 Colisão contra o carregador | p. 2
- 0.687 · 06 Perguntas frequentes sobre recarga | 1.8 Posso recarregar na chuva? | p. 1
- 0.680 · 03 Guia da plataforma EV ChargeOps | 4.1 Status das sessões | p. 1

