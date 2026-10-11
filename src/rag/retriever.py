"""Recuperação: busca os trechos mais parecidos com a pergunta e descarta os pouco relevantes.

Dois modos (RAG_BUSCA no .env ou em rag/config.py):
- "vetorial": só a busca semântica do Chroma (iterações 1 e 2 do eval);
- "hibrida": busca semântica + busca por palavra-chave (BM25), juntas pelo Reciprocal Rank Fusion.
"""
from collections import defaultdict
from dataclasses import asdict, dataclass

from langchain_core.documents import Document

from rag.bm25 import IndiceBM25
from rag.config import BUSCA, COLECAO, K, LIMIAR
from rag.vector_store import _cliente, buscar

# Busca híbrida
CANDIDATOS = 10  # quantos trechos de cada busca entram na fusão
RRF_K = 60       # constante do Reciprocal Rank Fusion: nota = soma de 1 / (60 + posição)
MIN_TERMOS = 2   # trecho que só o BM25 achou precisa ter ao menos 2 palavras da pergunta
PESO_BM25 = 1.0  # peso da lista do BM25 na fusão (1 = mesmo peso da semântica, o padrão do RRF)


@dataclass
class Trecho:
    texto: str       # conteúdo do chunk, sem a linha de cabeçalho
    documento: str   # título do PDF
    secao: str       # título da seção, com o número ("5.1 Falha de comunicação (...)")
    pagina: int
    arquivo: str
    nota: float      # similaridade de cosseno com a pergunta (quanto mais perto de 1, mais parecido)
    origem: str = "semântica"  # quem achou o trecho: "semântica", "palavra-chave" ou "as duas"


def _trecho(documento: Document, nota: float, origem: str = "semântica") -> Trecho:
    meta = documento.metadata
    cabecalho, _, texto = documento.page_content.partition("\n")
    return Trecho(
        texto=texto if cabecalho.startswith("[") else documento.page_content,
        documento=meta["documento"],
        secao=meta["secao"],
        pagina=meta["pagina"],
        arquivo=meta["arquivo"],
        nota=round(nota, 3),
        origem=origem,
    )


def recuperar(pergunta: str, k: int = K, limiar: float = LIMIAR, colecao: str = COLECAO,
              busca: str = BUSCA, peso_bm25: float = PESO_BM25) -> list[Trecho]:
    """Devolve até k trechos relevantes para a pergunta.

    O limiar não recusa a pergunta sozinho: ele só tira do prompt os trechos pouco
    parecidos. Uma pergunta sobre os dados do posto pode não ter trecho nenhum e
    ainda assim ter resposta nos dados operacionais.
    """
    if busca == "hibrida":
        return _recuperar_hibrida(pergunta, k, limiar, colecao, peso_bm25)
    return [_trecho(doc, nota) for doc, nota in buscar(pergunta, k=k, nome=colecao) if nota >= limiar]


_indices: dict[str, tuple[list[Document], IndiceBM25]] = {}


def _indice_bm25(colecao: str) -> tuple[list[Document], IndiceBM25]:
    """Índice BM25 da coleção, montado uma vez com os mesmos chunks que estão no Chroma.
    Se a ingestão rodar com o app aberto, é preciso reiniciar o app (como já é para o Chroma)."""
    if colecao not in _indices:
        dados = _cliente().get_collection(colecao).get(include=["documents", "metadatas"])
        docs = [Document(page_content=t, metadata=m) for t, m in zip(dados["documents"], dados["metadatas"])]
        _indices[colecao] = (docs, IndiceBM25([d.page_content for d in docs]))
    return _indices[colecao]


def _recuperar_hibrida(pergunta: str, k: int, limiar: float, colecao: str, peso_bm25: float) -> list[Trecho]:
    docs, indice = _indice_bm25(colecao)

    # Busca semântica em todos os chunks (são ~100): dá a similaridade de cada um, para o limiar e a tela
    semantica = buscar(pergunta, k=len(docs), nome=colecao)
    similaridade = {doc.metadata["chunk_id"]: nota for doc, nota in semantica}

    pontos = indice.pontuar(pergunta)
    ordem_bm25 = [i for i in sorted(range(len(docs)), key=lambda i: pontos[i], reverse=True) if pontos[i] > 0]

    fusao = defaultdict(float)
    origem = defaultdict(set)
    por_id = {d.metadata["chunk_id"]: d for d in docs}
    for posicao, (doc, _) in enumerate(semantica[:CANDIDATOS]):
        fusao[doc.metadata["chunk_id"]] += 1 / (RRF_K + posicao + 1)
        origem[doc.metadata["chunk_id"]].add("semântica")
    for posicao, i in enumerate(ordem_bm25[:CANDIDATOS]):
        chunk_id = docs[i].metadata["chunk_id"]
        fusao[chunk_id] += peso_bm25 / (RRF_K + posicao + 1)
        if indice.termos_em_comum(pergunta, i) >= MIN_TERMOS:
            origem[chunk_id].add("palavra-chave")

    # Entra o trecho parecido o bastante (limiar) ou achado pelo BM25 com 2+ palavras da pergunta
    aceitos = [c for c in fusao if similaridade.get(c, 0) >= limiar or "palavra-chave" in origem[c]]
    aceitos.sort(key=lambda c: fusao[c], reverse=True)

    def rotulo(chunk_id):
        quem = origem[chunk_id] if similaridade.get(chunk_id, 0) >= limiar else origem[chunk_id] - {"semântica"}
        return "as duas" if len(quem) == 2 else next(iter(quem), "semântica")

    return [_trecho(por_id[c], similaridade.get(c, 0.0), rotulo(c)) for c in aceitos[:k]]


def _neutralizar(texto: str) -> str:
    # Conteúdo de documento é informação, nunca instrução: um PDF que traga algo como
    # "<system>" ou "</trecho>" não pode fechar a tag do trecho nem imitar uma tag do prompt.
    return texto.replace("<", "‹").replace(">", "›")


def formatar_para_prompt(trechos: list[Trecho]) -> str:
    """Monta o bloco de documentos do prompt: cada trecho com documento, seção e página."""
    if not trechos:
        return "Nenhum trecho da base de conhecimento é relevante para esta pergunta."
    return "\n".join(
        f'<trecho id="{i}" documento="{t.documento}" secao="{t.secao}" pagina="{t.pagina}">\n'
        f"{_neutralizar(t.texto)}\n</trecho>"
        for i, t in enumerate(trechos, 1)
    )


def como_fontes(trechos: list[Trecho]) -> list[dict]:
    """Lista de fontes para a interface e para o eval."""
    return [asdict(t) for t in trechos]
