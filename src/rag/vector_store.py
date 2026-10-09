"""Banco vetorial persistente (Chroma) da base de conhecimento."""
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from rag.config import COLECAO, PASTA_CHROMA
from rag.embeddings import criar_embeddings


def _cliente():
    # Banco em disco, na pasta chroma_db/ da raiz do projeto
    return chromadb.PersistentClient(path=str(PASTA_CHROMA), settings=Settings(anonymized_telemetry=False))


def _existe(cliente, nome: str) -> bool:
    return nome in [colecao.name for colecao in cliente.list_collections()]


def recriar_colecao(chunks, nome: str = COLECAO) -> int:
    """Apaga a coleção antiga e grava os chunks de novo.

    Somar em vez de recriar duplicaria os trechos a cada ingestão,
    e a busca passaria a devolver o mesmo trecho repetido.
    """
    cliente = _cliente()
    if _existe(cliente, nome):
        cliente.delete_collection(nome)
    Chroma.from_documents(
        documents=chunks,
        embedding=criar_embeddings(),
        ids=[chunk.metadata["chunk_id"] for chunk in chunks],
        client=cliente,
        collection_name=nome,
        collection_metadata={"hnsw:space": "cosine"},  # compara os vetores por cosseno
    )
    return cliente.get_collection(nome).count()


def carregar_vector_store(nome: str = COLECAO) -> Chroma:
    """Abre uma coleção que já existe, sem gerar os embeddings de novo."""
    cliente = _cliente()
    if not _existe(cliente, nome):
        raise RuntimeError(f"A coleção '{nome}' ainda não existe. Rode antes: python src/rag/ingestao.py")
    return Chroma(client=cliente, collection_name=nome, embedding_function=criar_embeddings())


def buscar(pergunta: str, k: int = 4, nome: str = COLECAO):
    """Busca semântica: a pergunta vira vetor e o Chroma devolve os k chunks mais próximos.

    O Chroma devolve a distância de cosseno (0 = mesmo sentido); aqui ela vira
    similaridade (quanto mais perto de 1, mais parecido).
    """
    resultados = carregar_vector_store(nome).similarity_search_with_score(pergunta, k=k)
    return [(documento, 1 - distancia) for documento, distancia in resultados]
