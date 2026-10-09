"""Leitura dos PDFs da base com o PyMuPDFLoader: cada página vira um Document."""
import re
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document

# Textos que se repetem em todos os PDFs e não respondem pergunta nenhuma.
# Se ficassem, apareceriam iguais em vários chunks e atrapalhariam a busca.
_ROTULO = "ChargeGrid · Base de conhecimento"
_AVISO = re.compile(r"Documento simulado para fins acadêmicos.*?dados de demonstração do assistente\.", re.S)
_REVISAO = re.compile(r"^CG-[A-Z0-9-]+ · Revisão .*$", re.M)                # "CG-MAN-01 · Revisão 1 · maio de 2026"
_RODAPE = re.compile(r"^CG-[A-Z0-9-]+ · .* · p\. \d+/\d+$", re.M)           # "CG-MAN-01 · ... · p. 2/5"


def limpar_texto(texto: str) -> str:
    texto = texto.replace(_ROTULO, "")
    texto = _AVISO.sub("", texto)
    texto = _REVISAO.sub("", texto)
    texto = _RODAPE.sub("", texto)
    return re.sub(r"\n{2,}", "\n", texto).strip()


def carregar_pdfs(pasta: Path) -> list[Document]:
    """Lê todos os PDFs da pasta, em ordem de nome, e guarda de onde cada página veio."""
    paginas = []
    for pdf in sorted(Path(pasta).glob("*.pdf")):
        for pagina in PyMuPDFLoader(str(pdf)).load():
            paginas.append(Document(
                page_content=limpar_texto(pagina.page_content),
                metadata={
                    "documento": pagina.metadata.get("title") or pdf.stem,  # título gravado no PDF
                    "arquivo": pdf.name,
                    "pagina": pagina.metadata["page"] + 1,                   # o PyMuPDF conta a partir de 0
                },
            ))
    if not paginas:
        raise FileNotFoundError(f"Nenhum PDF encontrado em {pasta}")
    return paginas
