"""Configurações do RAG num lugar só: caminhos, modelo de embedding e tamanho dos chunks."""
import os
from pathlib import Path

# src/rag/config.py -> parents[2] é a raiz do projeto
RAIZ = Path(__file__).resolve().parents[2]

PASTA_BASE = RAIZ / "data" / "knowledge_base"   # PDFs da base de conhecimento
PASTA_CHROMA = RAIZ / "chroma_db"                # banco vetorial (está no .gitignore)
COLECAO = "chargegrid_kb"                        # nome da coleção dentro do Chroma

# Embeddings: nomic-embed-text no Ollama do próprio PC.
# No teste do bloco 0, o Ollama Cloud recusou esse modelo (401) com a mesma chave que funciona no chat.
MODELO_EMBEDDING = "nomic-embed-text"
OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434")

# Chunking: tamanho máximo de cada trecho e quanto um trecho repete do anterior (em caracteres).
# As iterações do eval comparam outras configurações (ex.: 500/50 e 1000/150).
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Recuperação: quantos trechos vão para o prompt (k) e a nota mínima para um trecho entrar.
# Valores escolhidos com o teste de busca (evals/teste_busca.py); as iterações do eval podem mudar.
K = 4
LIMIAR = 0.68
