"""Iteração 0 do eval: o assistente como ele estava na Sprint 3, sem RAG.

Reproduz a chain conversacional da Sprint 3 (src/chain/builder.py antes da Sprint 4):
- system prompt v2 (prompts/system_prompts/system_prompt_v2.md, que não mudou);
- o data/mock_data.json cru no prompt (o dicionário Python virava texto, sem formatação);
- gpt-oss:120b com temperature 0.2, top_p 0.9 e num_predict 512;
- histórico da conversa;
- sem base de conhecimento, sem guardrails (na Sprint 3 o import quebrado deixava os
  guardrails desligados) e sem router: as perguntas do eval vão todas para a chain
  conversacional, inclusive a do relatório semanal.

Serve só de "antes" para o eval. O app usa o fluxo novo (src/chain/builder.py).
"""
import os
import time

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from recursos import _carregar_dados_mock, _carregar_system_prompt

load_dotenv()

dados_mock = _carregar_dados_mock()
CONTEXTO = str(dados_mock)  # o que o modelo recebia na Sprint 3 (e o contexto que o RAGAS vai usar)

prompt = ChatPromptTemplate.from_messages([
    ("system", _carregar_system_prompt() + "\n\n" + "Contexto_operacional>\n" + "{contexto}\n"),
    ("placeholder", "{history}"),
    ("human", "Pergunta do operador: {pergunta}"),
])

llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL"),
    base_url=os.getenv("OLLAMA_BASE_URL", "https://ollama.com"),
    temperature=0.2,
    top_p=0.9,
    num_predict=512,
    client_kwargs={"headers": {"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"}},
)

chain = prompt | llm | StrOutputParser()

historicos: dict[str, list] = {}


def processar_pergunta(pergunta: str, session_id: str) -> dict:
    """Mesmo formato de retorno do src/chain/builder.py, para o eval tratar as iterações igual."""
    historico = historicos.setdefault(session_id, [])
    inicio = time.perf_counter()
    resposta = chain.invoke({"contexto": dados_mock, "history": historico, "pergunta": pergunta})
    historico += [HumanMessage(pergunta), AIMessage(resposta)]
    return {
        "resposta": resposta,
        "classificacao": "nao_estruturada",
        "fontes": [],
        "guardrail": None,
        "versao_prompt": "sprint3-v2",
        "latencia_resposta": time.perf_counter() - inicio,
    }
