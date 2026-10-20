# Base de conhecimento — ChargeGrid Assistant (Sprint 4)

Os 7 PDFs desta pasta são a base que o RAG indexa. São **documentos simulados**, escritos para o projeto: o ChargeGrid faz parte do EV Challenge 2026 (FIAP + GoodWe) e não tem documentação pública. Cada PDF traz esse aviso na primeira página.

| Arquivo | Código | Páginas | Conteúdo |
|---|---|---|---|
| `01_manual_operador_chargegrid.pdf` | CG-MAN-01 | 5 | status dos carregadores, tipos de alerta, procedimento para cada alerta, controle de demanda, manutenção, rotina diária, chamados |
| `02_especificacoes_carregadores.pdf` | CG-ESP-02 | 2 | modelo ChargeGrid DC-40, as 5 unidades, ramais, demanda contratada, compatibilidade |
| `03_guia_ev_chargeops.pdf` | CG-OPS-03 | 3 | plataforma de gestão: perfis, painel, sessões, alertas, cálculo dos indicadores de faturamento, relatório semanal |
| `04_tabela_tarifaria.pdf` | CG-TAR-04 | 2 | preço do kWh por faixa horária, regra de aplicação, ociosidade, falhas, bandeiras, pagamento, reembolso |
| `05_regimento_condominio_modelo.pdf` | CG-REG-05 | 3 | modelo de regimento de recarga compartilhada em condomínio: reservas, rateio, responsabilidades, penalidades |
| `06_faq_recarga.pdf` | CG-FAQ-06 | 2 | perguntas frequentes de motoristas e de operadores |
| `07_seguranca_emergencia.pdf` | CG-SEG-07 | 2 | o que o operador pode e não pode fazer, NR-10, procedimentos de emergência, telefones |

## Como a base foi montada

- **Coerente com `data/mock_data.json`:** 5 carregadores, limite de 40 kW nos carregadores 1 e 2 e de 32 kW nos 3, 4 e 5, horários de pico e de vale, códigos e níveis dos alertas, status das sessões. A tarifa intermediária (R$ 1,30/kWh) reproduz a SESS-004 (22,1 kWh → R$ 28,73), e a regra de sessão com falha explica a SESS-005 (R$ 0,00).
- **Seções numeradas** no próprio texto (`5.1 Falha de comunicação (falha_comunicacao, crítico)`): a citação "documento, seção" sai daí, e o código do alerta no título ajuda o retriever a achar o procedimento certo.
- **Cada seção se explica sozinha**, porque o retriever entrega o trecho isolado do resto do documento.
- **Lacunas de propósito:** peso, dimensões e garantia do carregador, a bandeira tarifária vigente e outros dados não estão na base, para testar se o assistente recusa em vez de inventar.
- Os números de referência (preços, limites, prazos) vêm de uma única fonte na hora de gerar os PDFs, para que nenhum documento contradiga outro.
- Os textos foram redigidos com apoio de IA e revisados pela equipe.

## Documento de teste (fora da base)

`evals/documentos_teste/CG-CT-2026-07_comunicado_firmware.pdf` contém instruções maliciosas plantadas e serve só para o teste de prompt injection vinda de documento. **Nunca copie esse arquivo para esta pasta.**
