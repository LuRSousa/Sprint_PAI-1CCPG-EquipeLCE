"""Recuperação: busca os trechos mais parecidos com a pergunta e descarta os pouco relevantes."""
from dataclasses import asdict, dataclass

from rag.config import COLECAO, K, LIMIAR
from rag.vector_store import buscar


@dataclass
class Trecho:
    texto: str       # conteúdo do chunk, sem a linha de cabeçalho
    documento: str   # título do PDF
    secao: str       # título da seção, com o número ("5.1 Falha de comunicação (...)")
    pagina: int
    arquivo: str
    nota: float      # similaridade de cosseno com a pergunta (quanto mais perto de 1, mais parecido)


def recuperar(pergunta: str, k: int = K, limiar: float = LIMIAR, colecao: str = COLECAO) -> list[Trecho]:
    """Devolve até k trechos com nota a partir do limiar.

    O limiar não recusa a pergunta sozinho: ele só tira do prompt os trechos pouco
    parecidos. Uma pergunta sobre os dados do posto pode não ter trecho nenhum e
    ainda assim ter resposta nos dados operacionais.
    """
    trechos = []
    for documento, nota in buscar(pergunta, k=k, nome=colecao):
        if nota < limiar:
            continue
        meta = documento.metadata
        cabecalho, _, texto = documento.page_content.partition("\n")
        trechos.append(Trecho(
            texto=texto if cabecalho.startswith("[") else documento.page_content,
            documento=meta["documento"],
            secao=meta["secao"],
            pagina=meta["pagina"],
            arquivo=meta["arquivo"],
            nota=round(nota, 3),
        ))
    return trechos


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
