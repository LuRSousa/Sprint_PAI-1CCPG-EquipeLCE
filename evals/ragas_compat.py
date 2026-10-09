"""RAGAS 0.4.3 ligado ao projeto: juiz no Ollama Cloud e embeddings do próprio RAG.

Três ajustes, todos explicados no relatório de avaliação:

1. O ragas 0.4.3 ainda importa `langchain_community.chat_models.vertexai`, que não existe
   no langchain-community 0.4.x. Sem o módulo vazio abaixo, o `import ragas` quebra.
   O módulo só é criado se o original não existir.
2. As instruções dos prompts do RAGAS estão em inglês. Sem pedir o idioma, o juiz escreve as
   perguntas da answer relevancy em inglês, e o nomic (o mesmo embedding do RAG) compara mal
   pergunta em inglês com pergunta em português: a nota cai sem a resposta ter piorado.
3. A answer relevancy compara pergunta com pergunta, então os dois lados recebem o prefixo
   "search_query:" do nomic (no RAG, trecho e pergunta recebem prefixos diferentes).

Usa a API "clássica" do RAGAS (ragas.metrics + LangchainLLMWrapper): a API nova
(ragas.metrics.collections) só aceita cliente compatível com OpenAI e recusa o ChatOllama.
"""
import asyncio
import contextlib
import os
import sys
import types
import warnings

# O RAGAS manda estatísticas de uso para o servidor dele por padrão
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")

try:
    import langchain_community.chat_models.vertexai  # noqa: F401
except ImportError:
    _modulo = types.ModuleType("langchain_community.chat_models.vertexai")

    class ChatVertexAI:  # só o nome que o ragas importa; nunca é usado
        pass

    _modulo.ChatVertexAI = ChatVertexAI
    sys.modules[_modulo.__name__] = _modulo

# Avisos de "API antiga" do próprio RAGAS e do langchain-community: a versão está fixada no requirements
warnings.filterwarnings("ignore", message=r".*ragas\.metrics.*deprecated.*")
warnings.filterwarnings("ignore", message=r".*langchain-community.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"ragas(\.|$)")

from langchain_ollama import ChatOllama  # noqa: E402
from ragas.dataset_schema import SingleTurnSample  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import AnswerRelevancy, Faithfulness  # noqa: E402
from ragas.run_config import RunConfig  # noqa: E402

from rag.embeddings import NomicEmbeddings  # noqa: E402
from rag.config import MODELO_EMBEDDING, OLLAMA_EMBED_URL  # noqa: E402

IDIOMA = (
    " Write every output text (statements, questions and reasons) in the same language as the"
    " answer being analyzed; the answers here are in Brazilian Portuguese."
)

# Retentativas curtas: limite de uso do Ollama Cloud não volta em poucos segundos,
# e o padrão do RAGAS (10 tentativas, até 60 s cada) deixaria o eval parado por minutos.
CONFIG_EXECUCAO = RunConfig(timeout=300, max_retries=3, max_wait=20, max_workers=2)


class FaithfulnessComDetalhes(Faithfulness):
    """A faithfulness do RAGAS, com a mesma conta, guardando as afirmações e os vereditos do juiz.

    O RAGAS devolve só a nota; para o relatório interessa saber QUAL frase da resposta não tem
    apoio no contexto. O eval avalia um item por vez, então guardar o último resultado basta.
    """

    async def _ascore(self, row, callbacks):
        self.ultimo_detalhe = []
        afirmacoes = (await self._create_statements(row, callbacks)).statements
        if not afirmacoes:
            return float("nan")
        vereditos = await self._create_verdicts(row, afirmacoes, callbacks)
        self.ultimo_detalhe = [
            {"afirmacao": v.statement, "apoiada": bool(v.verdict), "motivo": v.reason}
            for v in vereditos.statements
        ]
        return self._compute_score(vereditos)


class EmbeddingsPerguntas(NomicEmbeddings):
    """Embeddings para comparar pergunta com pergunta (answer relevancy): mesmo prefixo dos dois lados."""

    def embed_documents(self, texts):
        return super(NomicEmbeddings, self).embed_documents(["search_query: " + t for t in texts])

    async def aembed_documents(self, texts):
        return await super(NomicEmbeddings, self).aembed_documents(["search_query: " + t for t in texts])


_fila = None


class JuizUmPorVez(ChatOllama):
    """ChatOllama que faz uma chamada por vez. A answer relevancy pede as 3 perguntas ao mesmo
    tempo; em fila, o eval demora um pouco mais e não estoura o limite de requisições do Ollama Cloud."""

    async def _agenerate(self, *args, **kwargs):
        global _fila
        if _fila is None:
            _fila = asyncio.Semaphore(1)
        async with _fila:
            return await super()._agenerate(*args, **kwargs)


# Juiz fixo: na comparação de modelos (relatorio_modelos.md) o assistente muda e o juiz continua o mesmo,
# senão a nota mediria o juiz junto com o modelo avaliado. Dá para trocar com RAGAS_JUIZ no .env.
JUIZ_PADRAO = "gpt-oss:120b"


def modelo_juiz() -> str:
    return os.getenv("RAGAS_JUIZ") or JUIZ_PADRAO


def criar_juiz() -> ChatOllama:
    modelo = modelo_juiz()
    return JuizUmPorVez(
        model=modelo,
        base_url=os.getenv("OLLAMA_BASE_URL", "https://ollama.com"),
        temperature=0,       # o RAGAS sobrescreve: 0,01 numa chamada e 0,3 nas 3 perguntas da relevância
        num_predict=4096,    # o gpt-oss pensa antes de responder; com pouco espaço o JSON sai cortado
        reasoning="low" if modelo.startswith("gpt-oss") else None,  # julgamento simples, gasta menos cota
        client_kwargs={"headers": {"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"}},
    )


def _pedir_idioma(metrica):
    prompts = metrica.get_prompts()
    for prompt in prompts.values():
        if IDIOMA not in prompt.instruction:
            prompt.instruction += IDIOMA
    metrica.set_prompts(**prompts)


def criar_metricas():
    """Faithfulness e answer relevancy (3 perguntas geradas por resposta), prontas para usar.

    Cada métrica tem o seu juiz: o RAGAS muda a temperatura do modelo a cada chamada,
    e um juiz compartilhado misturaria as temperaturas das duas métricas.
    """
    embeddings = LangchainEmbeddingsWrapper(EmbeddingsPerguntas(model=MODELO_EMBEDDING, base_url=OLLAMA_EMBED_URL))
    fidelidade = FaithfulnessComDetalhes(llm=LangchainLLMWrapper(criar_juiz()))
    relevancia = AnswerRelevancy(llm=LangchainLLMWrapper(criar_juiz()), embeddings=embeddings, strictness=3)
    for metrica in (fidelidade, relevancia):
        _pedir_idioma(metrica)
        metrica.init(CONFIG_EXECUCAO)
    return fidelidade, relevancia


async def fechar_juizes(metricas) -> None:
    """Fecha as conexões dos juízes antes do fim do asyncio.run (no Windows, sem isso a saída
    termina com avisos de "Event loop is closed", que não mudam nada mas assustam)."""
    for metrica in metricas:
        juiz = getattr(metrica.llm, "langchain_llm", None)
        cliente = getattr(getattr(juiz, "_async_client", None), "_client", None)
        if cliente is not None:
            with contextlib.suppress(Exception):
                await cliente.aclose()


def montar_amostra(pergunta: str, resposta: str, contextos: list[str], referencia: str = "") -> SingleTurnSample:
    return SingleTurnSample(
        user_input=pergunta,
        response=resposta,
        retrieved_contexts=contextos,
        reference=referencia or None,
    )
