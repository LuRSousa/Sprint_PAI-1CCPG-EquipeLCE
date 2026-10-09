"""Ingestão da base: PDFs -> chunks -> embeddings -> Chroma.

Rode na raiz do projeto, com o Ollama aberto:
    python src/rag/ingestao.py
Para testar outra configuração de chunk:
    python src/rag/ingestao.py --chunk-size 500 --overlap 50
"""
import argparse
import sys
import time
from pathlib import Path

# Deixa a pasta src/ no caminho de import, como o app.py faz
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ollama import ResponseError  # noqa: E402

from rag.chunking import dividir_em_chunks  # noqa: E402
from rag.config import CHUNK_OVERLAP, CHUNK_SIZE, COLECAO, PASTA_BASE  # noqa: E402
from rag.loader import carregar_pdfs  # noqa: E402
from rag.vector_store import buscar, recriar_colecao  # noqa: E402

PERGUNTA_TESTE = "O carregador 2 está offline. O que o operador deve fazer?"


def main():
    parser = argparse.ArgumentParser(description="Recria o banco vetorial a partir dos PDFs da base.")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    parser.add_argument("--colecao", default=COLECAO)
    args = parser.parse_args()

    paginas = carregar_pdfs(PASTA_BASE)
    arquivos = {pagina.metadata["arquivo"] for pagina in paginas}
    print(f"PDFs lidos: {len(arquivos)} | páginas: {len(paginas)}")

    chunks = dividir_em_chunks(paginas, args.chunk_size, args.overlap)
    tamanhos = [len(chunk.page_content) for chunk in chunks]
    print(f"Chunks: {len(chunks)} (chunk_size={args.chunk_size}, overlap={args.overlap}) | "
          f"tamanho médio: {sum(tamanhos) // len(tamanhos)} caracteres | maior: {max(tamanhos)}")

    inicio = time.perf_counter()
    try:
        total = recriar_colecao(chunks, args.colecao)
    except ConnectionError:
        sys.exit("Não consegui falar com o Ollama. Abra o app do Ollama e rode de novo.")
    except ResponseError as erro:
        sys.exit(f"O Ollama recusou o pedido ({erro}). Se o modelo não estiver baixado: ollama pull nomic-embed-text")
    print(f"Coleção '{args.colecao}' recriada com {total} chunks em {time.perf_counter() - inicio:.1f} s")

    print(f"\nBusca de teste: {PERGUNTA_TESTE}")
    for documento, similaridade in buscar(PERGUNTA_TESTE, k=3, nome=args.colecao):
        meta = documento.metadata
        print(f"  {similaridade:.3f} | {meta['documento']} | {meta['secao']} | p. {meta['pagina']}")


if __name__ == "__main__":
    main()
