"""Divide as páginas em chunks sem misturar seções e marca de onde cada chunk veio."""
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Título de seção numerado no começo da linha, como "5.1 Falha de comunicação (falha_comunicacao, crítico)".
# Os PDFs da base foram escritos para que só os títulos tenham esse formato.
RE_TITULO_SECAO = re.compile(r"^(\d{1,2}(?:\.\d{1,2})?)\s+([A-ZÀ-Ý].*)$", re.M)


def _blocos_por_secao(paginas):
    """Quebra cada página nos títulos de seção.

    Devolve (seção, metadados da página, texto da seção naquela página). Uma seção que
    continua na página seguinte gera um bloco em cada página, os dois com a mesma seção.
    O texto antes do primeiro título do documento (título e subtítulo) fica de fora.
    """
    secao_atual = {}  # última seção vista em cada arquivo
    for pagina in paginas:
        arquivo = pagina.metadata["arquivo"]
        texto = pagina.page_content
        secao = secao_atual.get(arquivo)
        inicio = 0
        for titulo in list(RE_TITULO_SECAO.finditer(texto)) + [None]:
            fim = titulo.start() if titulo else len(texto)
            corpo = texto[inicio:fim].strip()
            if corpo and secao:
                yield secao, pagina.metadata, corpo
            if titulo:
                secao = titulo.group(0).strip()
                inicio = titulo.end()
        secao_atual[arquivo] = secao


def dividir_em_chunks(paginas, chunk_size: int, chunk_overlap: int) -> list[Document]:
    """Cada seção passa pelo RecursiveCharacterTextSplitter separadamente.

    Seção curta vira um chunk só; seção longa é cortada de preferência entre parágrafos,
    depois entre linhas, frases e palavras. A primeira linha do chunk diz de onde ele veio,
    o que ajuda a busca e deixa claro para o modelo qual é a fonte.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks, contador = [], {}
    for secao, meta, corpo in _blocos_por_secao(paginas):
        for parte in splitter.split_text(corpo):
            n = contador.get(meta["arquivo"], 0)
            contador[meta["arquivo"]] = n + 1
            chunks.append(Document(
                page_content=f"[{meta['documento']} | {secao}]\n{parte}",
                metadata={**meta, "secao": secao, "chunk_id": f"{meta['arquivo']}#{n:03d}"},
            ))
    return chunks
