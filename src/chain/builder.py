from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

from chain.memoria import criar_memoria, HistoricoTokenBuffer

from dotenv import load_dotenv
import os

from chain.router import classificar_prompt
from chain.structured_builder import executar_chain_estruturada

from recursos import (
    _carregar_dados_mock,
    _formatar_contexto_operacional,
    contar_tokens_entrada
)

# Sprint 4: RAG (recuperação na base de conhecimento + prompt versionado)
from rag.retriever import recuperar, formatar_para_prompt, como_fontes
from rag.prompt_rag import montar_prompt, VERSAO_PROMPT

import time
import tiktoken

# Objeto encoder/tokenizer
enc = tiktoken.get_encoding("cl100k_base")

# Carrega variáveis de ambiente
load_dotenv()

model = os.getenv("OLLAMA_MODEL")
model_router = os.getenv("OLLAMA_MODEL_ROUTER")
api_key = os.getenv("OLLAMA_API_KEY")
base_url = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")

# Dados do mock, já formatados como texto (na Sprint 3 o JSON cru ia para o prompt)
dados_mock = _carregar_dados_mock()
dados_formatados = _formatar_contexto_operacional(dados_mock)


# 1. Template: prompt RAG versionado (src/rag/prompt_rag.py) com histórico,
#    dados operacionais e trechos recuperados da base
prompt = montar_prompt()


# 2. Conexões dos modelos ao Ollama Cloud
llm = ChatOllama(
    model=model,
    base_url=base_url,
    temperature=0,      # Sprint 4: resposta presa ao contexto (antes 0.2)
    top_p=0.9,
    num_predict=1024,   # antes 512: a resposta agora traz as citações
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
)

llm_router = ChatOllama(
    model=model_router,
    base_url=base_url,
    temperature=0,
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
)


# 3. Parser: extrai somente o texto da resposta
parser = StrOutputParser()


# 4. Composição da chain conversacional
chain = prompt | llm | parser


# Memórias separadas por sessão
memorias_por_sessao = {}


def obter_memoria_por_sessao(session_id):
    """
    Recupera ou cria o histórico associado à sessão.

    O histórico utilizado pelo RunnableWithMessageHistory é um
    adaptador sobre ConversationTokenBufferMemory.
    """

    if session_id not in memorias_por_sessao:
        memoria = criar_memoria(llm)

        memorias_por_sessao[session_id] = HistoricoTokenBuffer(
            memoria
        )

    return memorias_por_sessao[session_id]


# 5. Adiciona gerenciamento automático de histórico à chain
chain_com_memoria = RunnableWithMessageHistory(
    chain,
    obter_memoria_por_sessao,
    input_messages_key="pergunta",
    history_messages_key="history",
)


def exibir_metricas_modelo(
    latencia_router,
    latencia_resposta,
    latencia_total,
    tokens_entrada,
    tokens_saida,
    tokens_router
):
    """Printa no terminal métricas de latência e tokens."""

    print("\n--- Métricas ---")

    print(f"Latência router: {latencia_router:.3f} s")

    print(f"Latência resposta: {latencia_resposta:.3f} s")

    print(f"Latência total: {latencia_total:.3f} s")

    print(f"Tokens entrada: {tokens_entrada}")

    print(f"Tokens router: {tokens_router}")

    print(
        f"Tokens saída: {tokens_saida}. "
        f"Total: {tokens_entrada + tokens_saida + tokens_router}"
    )


# Fonte da resposta da chain estruturada (relatório semanal): vem dos dados, não da base
FONTE_DADOS_SEMANA = {
    "texto": "",
    "documento": "Dados operacionais do posto",
    "secao": "Histórico dos últimos 7 dias",
    "pagina": None,
    "arquivo": "data/mock_data.json",
    "nota": None,
}


# 6. Processamento principal
def processar_pergunta(pergunta, session_id):

    inicio_router = time.perf_counter()

    classificacao, tokens_router = classificar_prompt(
        llm_router,
        pergunta
    )

    print(f"\nPergunta: {pergunta}")
    print(f"\nClassificação do prompt: {classificacao}")

    latencia_router = time.perf_counter() - inicio_router

    # Recupera o histórico da sessão para cálculo de tokens
    memoria = obter_memoria_por_sessao(session_id)

    history = memoria.messages

    # ============================================================
    # CHAIN NÃO ESTRUTURADA
    # ============================================================

    if classificacao == "nao_estruturada":

        # Recuperação: trechos da base parecidos com a pergunta (embeddings no Ollama local)
        inicio_busca = time.perf_counter()
        try:
            trechos = recuperar(pergunta)
        except ConnectionError:
            return {
                "resposta": (
                    "Não consegui consultar a base de conhecimento: o Ollama do computador "
                    "parece estar fechado. Abra o Ollama e tente de novo."
                ),
                "classificacao": classificacao,
                "fontes": [],
                "tokens_entrada": 0,
                "tokens_saida": 0,
                "tokens_router": tokens_router,
                "latencia_router": latencia_router,
                "latencia_busca": time.perf_counter() - inicio_busca,
                "latencia_resposta": 0,
                "latencia_total": latencia_router,
            }
        latencia_busca = time.perf_counter() - inicio_busca
        documentos = formatar_para_prompt(trechos)
        print(f"Trechos recuperados: {len(trechos)} (prompt RAG {VERSAO_PROMPT})")

        tokens_entrada = contar_tokens_entrada(
            history,
            pergunta,
            dados_mock
        ) + len(enc.encode(documentos))

        inicio_resposta = time.perf_counter()

        resposta = chain_com_memoria.invoke(
            {
                "dados_operacionais": dados_formatados,
                "documentos": documentos,
                "pergunta": pergunta,
            },
            config={
                "configurable": {
                    "session_id": session_id
                }
            }
        )

        latencia_resposta = (
            time.perf_counter() - inicio_resposta
        )

        tokens_saida = len(enc.encode(resposta))

        # Não chamar salvar_turno() aqui.
        # RunnableWithMessageHistory já gerencia o histórico.

        return {
            "resposta": resposta,
            "classificacao": classificacao,
            "fontes": como_fontes(trechos),
            "versao_prompt": VERSAO_PROMPT,
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida,
            "tokens_router": tokens_router,
            "latencia_router": latencia_router,
            "latencia_busca": latencia_busca,
            "latencia_resposta": latencia_resposta,
            "latencia_total": (
                latencia_router + latencia_busca + latencia_resposta
            ),
        }

    # ============================================================
    # CHAIN ESTRUTURADA
    # ============================================================

    elif classificacao == "estruturada":

        inicio_resposta = time.perf_counter()

        resposta, tokens_entrada, tokens_saida = (
            executar_chain_estruturada(
                history,
                pergunta
            )
        )

        latencia_resposta = (
            time.perf_counter() - inicio_resposta
        )

        return {
            "resposta": resposta,
            "classificacao": classificacao,
            "fontes": [FONTE_DADOS_SEMANA],
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida,
            "tokens_router": tokens_router,
            "latencia_router": latencia_router,
            "latencia_resposta": latencia_resposta,
            "latencia_total": (
                latencia_router + latencia_resposta
            ),
        }

    # ============================================================
    # CLASSIFICAÇÃO INVÁLIDA
    # ============================================================

    else:

        return {
            "resposta": (
                "Tivemos um problema em processar sua mensagem. "
                "Por favor, tente novamente."
            ),
            "classificacao": classificacao,
            "fontes": [],
            "tokens_entrada": 0,
            "tokens_saida": 0,
            "tokens_router": tokens_router,
            "latencia_router": latencia_router,
            "latencia_resposta": 0,
            "latencia_total": latencia_router,
        }