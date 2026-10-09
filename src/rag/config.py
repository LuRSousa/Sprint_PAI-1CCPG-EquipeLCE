"""Configurações do RAG num lugar só: caminhos, modelo de embedding e tamanho dos chunks."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Lê o .env da raiz antes de tudo, para OLLAMA_EMBED_URL, RAG_COLECAO e RAG_PROMPT_VERSAO valerem
load_dotenv()

# src/rag/config.py -> parents[2] é a raiz do projeto
RAIZ = Path(__file__).resolve().parents[2]

PASTA_BASE = RAIZ / "data" / "knowledge_base"   # PDFs da base de conhecimento
PASTA_CHROMA = RAIZ / "chroma_db"                # banco vetorial (está no .gitignore)
# Coleção usada pelo assistente. O teste de segurança troca pela coleção com o documento de injeção.
COLECAO = os.getenv("RAG_COLECAO", "chargegrid_kb")

# Documento de teste com injeção plantada: fica fora da base e só entra na coleção de teste
PASTA_TESTE_INJECAO = RAIZ / "evals" / "documentos_teste"
COLECAO_TESTE_INJECAO = "teste_injecao"

# Embeddings: nomic-embed-text no Ollama do próprio PC.
# No teste do bloco 0, o Ollama Cloud recusou esse modelo (401) com a mesma chave que funciona no chat.
MODELO_EMBEDDING = "nomic-embed-text"
OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434")

# Chunking: tamanho máximo de cada trecho e quanto um trecho repete do anterior (em caracteres).
# As iterações do eval comparam outras configurações (ex.: 500/50 e 1000/150).
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Recuperação: quantos trechos vão para o prompt (k) e a nota mínima para um trecho entrar.
# Valores escolhidos com o teste de busca (evals/teste_busca.py). As iterações do eval podem
# trocar pelo .env (RAG_K e RAG_LIMIAR) sem mexer no código.
K = int(os.getenv("RAG_K", "4"))
LIMIAR = float(os.getenv("RAG_LIMIAR", "0.68"))

# Versão do prompt RAG usada pela chain (src/rag/prompt_rag.py). O eval troca para comparar versões.
VERSAO_PROMPT = os.getenv("RAG_PROMPT_VERSAO", "v1")
