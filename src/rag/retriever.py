"""Recuperação: busca os trechos mais parecidos com a pergunta e descarta os pouco relevantes.

Três modos (RAG_BUSCA no .env ou em rag/config.py):
- "vetorial": só a busca semântica do Chroma (iterações 1 e 2 do eval);
- "hibrida": busca semântica + busca por palavra-chave (BM25), juntas pelo Reciprocal Rank Fusion
  (iteração 3). Na RRF, o trecho que aparece nas duas listas sempre fica na frente; no eval, isso
  empurrou para fora dos 4 trechos o acerto exato da palavra-chave ("choque elétrico", "noite inteira");
- "intercalada": as mesmas duas buscas, com as vagas divididas: 1º da semântica, 1º do BM25,
  2º da semântica, 2º do BM25... (iteração 4). É o padrão do app: foi a que mais acertou no eval.
"""
from itertools import zip_longest
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
              busca: str = BUSCA) -> list[Trecho]:
    """Devolve até k trechos relevantes para a pergunta.

    O limiar não recusa a pergunta sozinho: ele só tira do prompt os trechos pouco
    parecidos. Uma pergunta sobre os dados do posto pode não ter trecho nenhum e
    ainda assim ter resposta nos dados operacionais.
    """
    if busca in ("hibrida", "intercalada"):
        return _recuperar_hibrida(pergunta, k, limiar, colecao, intercalar=busca == "intercalada")
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


def _recuperar_hibrida(pergunta: str, k: int, limiar: float, colecao: str, intercalar: bool) -> list[Trecho]:
    docs, indice = _indice_bm25(colecao)
    por_id = {d.metadata["chunk_id"]: d for d in docs}

    # Busca semântica em todos os chunks (são ~100): dá a similaridade de cada um, para o limiar e a tela
    semantica = buscar(pergunta, k=len(docs), nome=colecao)
    similaridade = {doc.metadata["chunk_id"]: nota for doc, nota in semantica}
    lista_semantica = [doc.metadata["chunk_id"] for doc, _ in semantica[:CANDIDATOS]]

    pontos = indice.pontuar(pergunta)
    ordem = [i for i in sorted(range(len(docs)), key=lambda i: pontos[i], reverse=True) if pontos[i] > 0]
    lista_bm25 = [docs[i].metadata["chunk_id"] for i in ordem[:CANDIDATOS]]
    chave_forte = {docs[i].metadata["chunk_id"] for i in ordem[:CANDIDATOS]
                   if indice.termos_em_comum(pergunta, i) >= MIN_TERMOS}

    # Entra o trecho parecido o bastante (limiar) ou achado pelo BM25 com 2+ palavras da pergunta
    def aceito(chunk_id):
        return similaridade.get(chunk_id, 0) >= limiar or chunk_id in chave_forte

    if intercalar:
        escolhidos = []
        for da_semantica, do_bm25 in zip_longest(lista_semantica, lista_bm25):
            for chunk_id in (da_semantica, do_bm25):
                if chunk_id and chunk_id not in escolhidos and aceito(chunk_id):
                    escolhidos.append(chunk_id)
    else:
        fusao = defaultdict(float)
        for lista in (lista_semantica, lista_bm25):
            for posicao, chunk_id in enumerate(lista):
                fusao[chunk_id] += 1 / (RRF_K + posicao + 1)
        escolhidos = sorted((c for c in fusao if aceito(c)), key=lambda c: fusao[c], reverse=True)

    def origem(chunk_id):
        pela_semantica = similaridade.get(chunk_id, 0) >= limiar and chunk_id in lista_semantica
        pela_chave = chunk_id in chave_forte
        return "as duas" if pela_semantica and pela_chave else ("palavra-chave" if pela_chave else "semântica")

    return [_trecho(por_id[c], similaridade.get(c, 0.0), origem(c)) for c in escolhidos[:k]]


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
