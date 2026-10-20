"""Faz perguntas ao assistente pelo terminal, sem o Streamlit, e mostra resposta, fontes e métricas.

Rode na raiz do projeto, com o Ollama aberto (embeddings) e a chave no .env (chat):
    python evals/perguntar.py "O carregador 2 está offline. O que eu faço?"
Sem pergunta na linha de comando, ele abre uma conversa (as perguntas seguintes usam a memória).
Para sair da conversa, aperte Enter sem digitar nada.
"""
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from chain.builder import processar_pergunta  # noqa: E402


def mostrar(resultado):
    print("\n" + resultado["resposta"].strip())
    fontes = [f for f in resultado.get("fontes", []) if f.get("nota") is not None]
    if fontes:
        print("\nTrechos usados no prompt:")
        for f in fontes:
            print(f"  {f['nota']:.3f} | {f['documento']} | {f['secao']} | p. {f['pagina']}")
    elif resultado.get("classificacao") == "nao_estruturada":
        print("\nNenhum trecho da base passou no limiar (só os dados operacionais foram para o prompt).")
    print(f"\nRota: {resultado.get('classificacao')} | prompt: {resultado.get('versao_prompt', '-')} | "
          f"tempo total: {resultado.get('latencia_total', 0):.1f} s")


def main():
    sessao = str(uuid.uuid4())
    if len(sys.argv) > 1:
        mostrar(processar_pergunta(" ".join(sys.argv[1:]), sessao))
        return
    while True:
        pergunta = input("\nPergunta (Enter para sair): ").strip()
        if not pergunta:
            break
        mostrar(processar_pergunta(pergunta, sessao))


if __name__ == "__main__":
    main()
