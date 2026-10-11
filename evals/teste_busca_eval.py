"""Qualidade do contexto recuperado, por forma de busca, nas perguntas do eval set.

Para cada pergunta com seções esperadas (fontes_esperadas), mostra se a busca trouxe uma delas
entre os k trechos que vão para o prompt, e em que posição. Não chama nenhum LLM: só os
embeddings do Ollama do computador.

Formas comparadas:
  vetorial            só a busca semântica (iterações 1 e 2 do eval)
  bm25                só a busca por palavra-chave
  híbrida             semântica + BM25, juntas pelo Reciprocal Rank Fusion
  vetorial + consulta busca semântica com a pergunta completada pela conversa e pelos dados
  híbrida + consulta  as duas coisas (iteração 3 do eval)
  intercalada + consulta  semântica + BM25 com as vagas divididas entre as duas (iteração 4)

Também confere as perguntas fora do domínio: quantos trechos passariam para o prompt
(o ideal é nenhum, para o guardrail de escopo continuar barrando).

    python evals/teste_busca_eval.py
Resultado em evals/resultados/teste_busca_eval.md
"""
import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from langchain_core.messages import HumanMessage  # noqa: E402

from rag.config import COLECAO, K, LIMIAR  # noqa: E402
from rag.consulta import montar_consulta  # noqa: E402
from rag.retriever import _indice_bm25, recuperar  # noqa: E402
from recursos import _carregar_dados_mock  # noqa: E402

EVAL_SET = RAIZ / "evals" / "eval_set_sprint4.json"
DESTINO = RAIZ / "evals" / "resultados" / "teste_busca_eval.md"
FORMAS = ["vetorial", "bm25", "híbrida", "vetorial + consulta", "híbrida + consulta", "intercalada + consulta"]


def _bate(trecho_arquivo: str, trecho_secao: str, esperadas) -> bool:
    numero = (trecho_secao or "").split(" ")[0]
    return any(trecho_arquivo[:2] == arq and (numero == sec or numero.startswith(sec + "."))
               for arq, sec in esperadas)


def _bm25(texto: str, k: int):
    """Só palavra-chave: os k trechos com maior pontuação (e com ao menos 2 palavras da pergunta)."""
    docs, indice = _indice_bm25(COLECAO)
    pontos = indice.pontuar(texto)
    ordem = [i for i in sorted(range(len(docs)), key=lambda i: pontos[i], reverse=True)
             if pontos[i] > 0 and indice.termos_em_comum(texto, i) >= 2]
    return [(docs[i].metadata["arquivo"], docs[i].metadata["secao"]) for i in ordem[:k]]


def buscar_por_forma(forma: str, pergunta: str, historico, dados) -> list[tuple[str, str]]:
    texto = montar_consulta(pergunta, historico, dados) if forma.endswith("consulta") else pergunta
    if forma == "bm25":
        return _bm25(texto, K)
    busca = forma.split(" ")[0].replace("í", "i")  # "vetorial", "hibrida" ou "intercalada"
    return [(t.arquivo, t.secao) for t in recuperar(texto, busca=busca)]


def main():
    itens = json.loads(EVAL_SET.read_text(encoding="utf-8"))["itens"]
    dados = _carregar_dados_mock()
    acertos = {f: 0 for f in FORMAS}
    linhas = [
        "# Busca: qualidade do contexto recuperado",
        "",
        f"- Data: {datetime.now():%d/%m/%Y %H:%M} · coleção `{COLECAO}` · k = {K} · limiar {LIMIAR}",
        "- Célula: posição da primeira seção esperada entre os trechos que vão para o prompt (– = nenhuma).",
        "",
        "| Item | Seções esperadas | " + " | ".join(FORMAS) + " |",
        "|---|---|" + "---|" * len(FORMAS),
    ]
    com_fonte = [it for it in itens if it["fontes_esperadas"]]
    for item in com_fonte:
        pergunta = item["turnos"][-1]
        historico = [HumanMessage(t) for t in item["turnos"][:-1]]
        celulas = []
        for forma in FORMAS:
            trechos = buscar_por_forma(forma, pergunta, historico, dados)
            posicao = next((i for i, (arq, sec) in enumerate(trechos, 1) if _bate(arq, sec, item["fontes_esperadas"])), None)
            acertos[forma] += posicao is not None
            celulas.append(f"{posicao}º" if posicao else "–")
        esperadas = ", ".join(f"{a} §{s}" for a, s in item["fontes_esperadas"])
        linhas.append(f"| {item['id']} | {esperadas} | " + " | ".join(celulas) + " |")
    total = len(com_fonte)
    linhas.append("| **Acertos** | | " + " | ".join(f"**{acertos[f]}/{total}**" for f in FORMAS) + " |")

    linhas += ["", "## Perguntas fora do domínio (trechos que passariam para o prompt)", "",
               "| Item | Pergunta | " + " | ".join(FORMAS) + " |", "|---|---|" + "---|" * len(FORMAS)]
    for item in [it for it in itens if it["categoria"] in ("fora do escopo",)]:
        pergunta = item["turnos"][-1]
        contagens = [str(len(buscar_por_forma(f, pergunta, [], dados))) for f in FORMAS]
        linhas.append(f"| {item['id']} | {pergunta} | " + " | ".join(contagens) + " |")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    for forma in FORMAS:
        print(f"{forma:22} {acertos[forma]}/{total}")
    print(f"\nResultado em {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
