# ChargeGrid Assistant: como rodar (Sprint 4)

Assistente com RAG: responde sobre o posto usando os dados operacionais (`data/mock_data.json`) e a base de conhecimento em PDF (`data/knowledge_base/`), citando a fonte de cada informação.

## O que precisa estar instalado

- **Python 3.10 ou mais novo** (testado no 3.14, Windows).
- **Ollama** instalado e aberto no computador: é ele que gera os embeddings, com o `nomic-embed-text`.
- **Chave do Ollama Cloud**: o modelo de conversa (`gpt-oss:120b`) roda na nuvem.

## 1. Ambiente

Na raiz do projeto (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Chave e modelos

```powershell
copy .env.example .env
code .env
```

No `.env`, troque o valor de `OLLAMA_API_KEY` pela sua chave, sem aspas e sem espaço. O `.env` está no `.gitignore` e nunca deve ir para o repositório.

```powershell
ollama pull nomic-embed-text
```

## 3. Ingestão da base (uma vez, e de novo sempre que um PDF mudar)

```powershell
python src/rag/ingestao.py
```

O esperado: `PDFs lidos: 7 | páginas: 19`, `Varredura de injeção: 0 trecho(s) em quarentena` e `Coleção 'chargegrid_kb' recriada com 104 chunks`. O banco fica em `chroma_db/`, que não vai para o repositório e é recriado por esse comando.

## 4. Interface

```powershell
streamlit run app/app.py
```

Cada resposta traz a citação no texto e, embaixo, o botão **Fontes** com o documento, a seção, a página, a similaridade e o trecho usado. Quando um guardrail responde no lugar do modelo, aparece qual foi.

## 5. Testes

| Comando | O que mostra |
|---|---|
| `python evals/teste_busca.py` | se a busca acha a seção certa (sem LLM), com as notas de similaridade |
| `python evals/perguntar.py "sua pergunta"` | a resposta pelo terminal, com os trechos usados |
| `python src/rag/ingestao.py --incluir-teste-injecao` e depois `python evals/teste_seguranca.py` | injeção vinda de documento, ataques na pergunta, escopo e especificação inexistente |
| `python evals/avaliar.py --iteracao 1` | o eval completo: 24 perguntas com gabarito, verificações automáticas e RAGAS (faithfulness e answer relevancy). Detalhes em `evals/README.md` |

Os resultados ficam em `evals/resultados/`.

## Como a resposta é montada

```
pergunta
  → guardrail de entrada (jailbreak, injeção)
  → busca no Chroma: 4 trechos mais parecidos, só os com nota ≥ 0,68
  → guardrail de escopo e de pedidos de risco
  → router: relatório semanal (chain estruturada) ou conversa (chain RAG)
  → prompt RAG versionado: dados do posto + trechos com documento, seção e página
  → gpt-oss:120b (temperature 0) com memória da conversa
  → guardrail de saída (vazamento de instruções)
  → resposta com citação + fontes na tela
```

| Pasta | O que tem |
|---|---|
| `src/rag/` | `loader.py`, `chunking.py`, `embeddings.py`, `vector_store.py`, `retriever.py`, `prompt_rag.py`, `varredura.py`, `ingestao.py` e `config.py` (todos os parâmetros num lugar só) |
| `src/chain/` | router, chain estruturada, memória e `builder.py`, que liga tudo |
| `src/guardrails/` | moderação (jailbreak e injeção), escopo e filtro de saída |
| `data/knowledge_base/` | os 7 PDFs simulados da base, com um README explicando como foram montados |
| `evals/` | testes e resultados |

## Problemas comuns

| Mensagem | O que fazer |
|---|---|
| `Failed to connect to Ollama` ou "o Ollama do computador parece estar fechado" | abrir o app do Ollama |
| `unauthorized (status code: 401)` | conferir a `OLLAMA_API_KEY` no `.env` e reiniciar o app |
| "A coleção 'chargegrid_kb' ainda não existe" | rodar a ingestão (passo 3) |
| respostas estranhas depois de rodar a ingestão com o app aberto | parar o Streamlit (Ctrl+C) e abrir de novo |
