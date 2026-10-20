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
from rag.consulta import montar_consulta
from rag.config import BUSCA
from rag.prompt_rag import montar_prompt, VERSAO_PROMPT

# Sprint 4: guardrails da Sprint 3, agora ligados na entrada e na saída
from guardrails.moderation import moderar, filtrar_saida
from guardrails.scope_validator import validar_escopo

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
    # antes 512: a resposta agora traz as citações. O gpt-oss raciocina antes de responder e esse
    # raciocínio conta no limite; o eval troca o valor com --max-tokens (OLLAMA_NUM_PREDICT)
    num_predict=int(os.getenv("OLLAMA_NUM_PREDICT", "1024")),
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


def _resultado(resposta, classificacao, fontes=None, guardrail=None, **extras):
    """Formato único de retorno de processar_pergunta (o app usa "resposta"; o eval usa o resto)."""
    base = {
        "resposta": resposta,
        "classificacao": classificacao,
        "fontes": fontes or [],
        "guardrail": guardrail,
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "tokens_router": 0,
        "latencia_router": 0,
        "latencia_busca": 0,
        "latencia_resposta": 0,
    }
    base.update(extras)
    base["latencia_total"] = base["latencia_router"] + base["latencia_busca"] + base["latencia_resposta"]
    return base


def _filtrar_saida(resposta):
    """Guardrail de saída: não deixa passar resposta com pedaço das instruções internas."""
    saida = filtrar_saida(resposta)
    if saida.bloqueada:
        print(f"Guardrail de saída: {saida.categoria}")
        return saida.mensagem_usuario, saida.categoria
    return resposta, None


# 6. Processamento principal
def processar_pergunta(pergunta, session_id):
    """Fluxo da Sprint 4:
    guardrail (jailbreak/injeção) -> busca na base -> guardrail de escopo -> router
    -> chain (RAG ou estruturada) -> guardrail de saída.
    """

    print(f"\nPergunta: {pergunta}")

    # Histórico da sessão (para o escopo e para a contagem de tokens)
    memoria = obter_memoria_por_sessao(session_id)
    history = memoria.messages

    # 1. Guardrail de entrada: jailbreak e injeção na pergunta, antes de qualquer chamada de modelo
    bloqueio = moderar(pergunta)
    if bloqueio.bloqueada:
        print(f"Guardrail de entrada: {bloqueio.categoria}")
        return _resultado(bloqueio.mensagem_usuario, "bloqueada", guardrail=bloqueio.categoria)

    # 2. Recuperação: trechos da base parecidos com a pergunta (embeddings no Ollama local).
    #    Nas buscas híbridas, o texto da busca é a pergunta completada com a conversa e os dados do
    #    posto (rag/consulta.py); o modelo continua recebendo a pergunta original.
    inicio_busca = time.perf_counter()
    consulta = montar_consulta(pergunta, history, dados_mock) if BUSCA != "vetorial" else pergunta
    try:
        trechos = recuperar(consulta)
    except ConnectionError:
        return _resultado(
            "Não consegui consultar a base de conhecimento: o Ollama do computador "
            "parece estar fechado. Abra o Ollama e tente de novo.",
            "erro",
            latencia_busca=time.perf_counter() - inicio_busca,
        )
    latencia_busca = time.perf_counter() - inicio_busca

    # 3. Guardrail de escopo e de pedidos de risco (elétrico, jurídico, financeiro).
    #    Sem palavra do domínio, a pergunta ainda passa se a busca achou trecho relevante
    #    ou se ela continua a conversa ("E o 4?").
    bloqueio = validar_escopo(pergunta, contexto_relevante=bool(trechos) or bool(history))
    if bloqueio.bloqueada:
        print(f"Guardrail de entrada: {bloqueio.categoria}")
        return _resultado(bloqueio.mensagem_usuario, "bloqueada", guardrail=bloqueio.categoria,
                          latencia_busca=latencia_busca)

    # 4. Router: relatório semanal (estruturada) ou conversa com RAG (não estruturada)
    inicio_router = time.perf_counter()
    classificacao, tokens_router = classificar_prompt(
        llm_router,
        pergunta
    )
    latencia_router = time.perf_counter() - inicio_router
    print(f"Classificação do prompt: {classificacao}")

    # ============================================================
    # CHAIN NÃO ESTRUTURADA (RAG)
    # ============================================================

    if classificacao == "nao_estruturada":

        documentos = formatar_para_prompt(trechos)
        print(f"Trechos recuperados: {len(trechos)} (prompt RAG {VERSAO_PROMPT}, busca {BUSCA})")

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

        latencia_resposta = time.perf_counter() - inicio_resposta
        tokens_saida = len(enc.encode(resposta))

        # Não chamar salvar_turno() aqui.
        # RunnableWithMessageHistory já gerencia o histórico.

        resposta, guardrail = _filtrar_saida(resposta)

        return _resultado(
            resposta, classificacao,
            fontes=como_fontes(trechos),
            guardrail=guardrail,
            versao_prompt=VERSAO_PROMPT,
            consulta_busca=consulta,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            tokens_router=tokens_router,
            latencia_router=latencia_router,
            latencia_busca=latencia_busca,
            latencia_resposta=latencia_resposta,
        )

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

        latencia_resposta = time.perf_counter() - inicio_resposta

        resposta, guardrail = _filtrar_saida(resposta)

        return _resultado(
            resposta, classificacao,
            fontes=[FONTE_DADOS_SEMANA],
            guardrail=guardrail,
            tokens_entrada=tokens_entrada,
            tokens_saida=tokens_saida,
            tokens_router=tokens_router,
            latencia_router=latencia_router,
            latencia_busca=latencia_busca,
            latencia_resposta=latencia_resposta,
        )

    # ============================================================
    # CLASSIFICAÇÃO INVÁLIDA
    # ============================================================

    else:

        return _resultado(
            "Tivemos um problema em processar sua mensagem. Por favor, tente novamente.",
            classificacao,
            tokens_router=tokens_router,
            latencia_router=latencia_router,
            latencia_busca=latencia_busca,
        )
