"""Embeddings com o nomic-embed-text, rodando no Ollama do PC (mesma ideia do CP2)."""
from langchain_ollama import OllamaEmbeddings

from rag.config import MODELO_EMBEDDING, OLLAMA_EMBED_URL


class NomicEmbeddings(OllamaEmbeddings):
    # O nomic-embed-text foi treinado com um prefixo que diz o papel do texto:
    # "search_document:" nos trechos guardados e "search_query:" nas perguntas.
    # Sem o prefixo, as similaridades ficam espremidas e a ordem dos resultados piora.
    def embed_documents(self, texts):
        return super().embed_documents(["search_document: " + texto for texto in texts])

    def embed_query(self, text):
        # O embed_query original chama self.embed_documents, que colocaria o prefixo errado.
        return super().embed_documents(["search_query: " + text])[0]

    async def aembed_documents(self, texts):
        return await super().aembed_documents(["search_document: " + texto for texto in texts])

    async def aembed_query(self, text):
        return (await super().aembed_documents(["search_query: " + text]))[0]


def criar_embeddings() -> NomicEmbeddings:
    # O mesmo modelo transforma os chunks e as perguntas em vetores de 768 números.
    # Se trocar o modelo ou os prefixos, é preciso rodar a ingestão de novo.
    return NomicEmbeddings(model=MODELO_EMBEDDING, base_url=OLLAMA_EMBED_URL)
