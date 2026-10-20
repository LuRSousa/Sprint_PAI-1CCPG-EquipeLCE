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

    python evals/teste_busca_eval.py                       # k do src/rag/config.py
    python evals/teste_busca_eval.py --varrer-k 2,3,4,6,8  # quantos trechos levar para o prompt
Resultados em evals/resultados/teste_busca_eval.md e teste_busca_k.md
"""
import argparse
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
DESTINO_K = RAIZ / "evals" / "resultados" / "teste_busca_k.md"
FORMAS = ["vetorial", "bm25", "híbrida", "vetorial + consulta", "híbrida + consulta", "intercalada + consulta"]
FORMA_DO_APP = "intercalada + consulta"


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
    return [(docs[i].metadata["arquivo"], docs[i].metadata["secao"], len(docs[i].page_content)) for i in ordem[:k]]


def buscar_por_forma(forma: str, pergunta: str, historico, dados, k: int = K) -> list[tuple[str, str, int]]:
    """Trechos que iriam para o prompt: (arquivo, seção, tamanho do texto em caracteres)."""
    texto = montar_consulta(pergunta, historico, dados) if forma.endswith("consulta") else pergunta
    if forma == "bm25":
        return _bm25(texto, k)
    busca = forma.split(" ")[0].replace("í", "i")  # "vetorial", "hibrida" ou "intercalada"
    return [(t.arquivo, t.secao, len(t.texto)) for t in recuperar(texto, k=k, busca=busca)]


def _posicao(trechos, esperadas):
    return next((i for i, (arq, sec, _) in enumerate(trechos, 1) if _bate(arq, sec, esperadas)), None)


def _br(numero: float, casas: int = 0) -> str:
    texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


def varrer_k(valores: list[int]):
    """Para cada k: acertos de cada forma de busca e, na forma do app, o tamanho do contexto."""
    itens = json.loads(EVAL_SET.read_text(encoding="utf-8"))["itens"]
    dados = _carregar_dados_mock()
    com_fonte = [it for it in itens if it["fontes_esperadas"]]
    fora = [it for it in itens if it["categoria"] == "fora do escopo"]
    total = len(com_fonte)
    linhas = [
        "# Busca: quantos trechos levar para o prompt (k)",
        "",
        f"- Data: {datetime.now():%d/%m/%Y %H:%M} · coleção `{COLECAO}` · limiar {LIMIAR} · k em uso: {K}",
        f"- Acertos: perguntas (de {total}) em que uma seção esperada está entre os trechos que vão para o prompt.",
        "",
        "| k | " + " | ".join(FORMAS) + " |",
        "|---|" + "---|" * len(FORMAS),
    ]
    app = []
    for k in valores:
        acertos = {f: 0 for f in FORMAS}
        trechos_app, caracteres_app, faltam = [], [], []
        for item in com_fonte:
            pergunta = item["turnos"][-1]
            historico = [HumanMessage(t) for t in item["turnos"][:-1]]
            for forma in FORMAS:
                trechos = buscar_por_forma(forma, pergunta, historico, dados, k)
                achou = _posicao(trechos, item["fontes_esperadas"]) is not None
                acertos[forma] += achou
                if forma == FORMA_DO_APP:
                    trechos_app.append(len(trechos))
                    caracteres_app.append(sum(t[2] for t in trechos))
                    if not achou:
                        faltam.append(item["id"])
        fora_app = [len(buscar_por_forma(FORMA_DO_APP, it["turnos"][-1], [], dados, k)) for it in fora]
        linhas.append(f"| {k} | " + " | ".join(f"{acertos[f]}/{total}" for f in FORMAS) + " |")
        app.append((k, acertos[FORMA_DO_APP], sum(trechos_app) / total, sum(caracteres_app) / total, fora_app, faltam))
        print(f"k = {k}: {FORMA_DO_APP} {acertos[FORMA_DO_APP]}/{total}")

    linhas += ["", f"## Na busca do app ({FORMA_DO_APP})", "",
               "| k | Acertos | Trechos por pergunta (média) | Caracteres de trecho por pergunta (média) "
               "| Trechos nas perguntas fora do domínio | Perguntas sem seção esperada |",
               "|---|---|---|---|---|---|"]
    for k, acertos, trechos, caracteres, fora_app, faltam in app:
        linhas.append(f"| {k} | {acertos}/{total} | {_br(trechos, 1)} | {_br(caracteres)} | "
                      f"{' e '.join(map(str, fora_app)) or '–'} | {', '.join(faltam) or '–'} |")
    linhas += ["", "Cada caractere a mais de trecho também é token de entrada a mais em toda pergunta "
               "(em português, algo perto de 4 caracteres por token)."]
    DESTINO_K.parent.mkdir(parents=True, exist_ok=True)
    DESTINO_K.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\nResultado em {DESTINO_K.relative_to(RAIZ)}")


def main():
    parser = argparse.ArgumentParser(description="Qualidade da busca nas perguntas do eval set (sem LLM)")
    parser.add_argument("--varrer-k", help="valores de k separados por vírgula (ex.: 2,3,4,6,8)")
    args = parser.parse_args()
    if args.varrer_k:
        varrer_k([int(v) for v in args.varrer_k.split(",") if v.strip()])
        return

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
            posicao = _posicao(trechos, item["fontes_esperadas"])
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
    try:
        main()
    except ConnectionError:
        # os embeddings da busca vêm do Ollama do computador; sem ele, nenhuma forma de busca roda
        raise SystemExit("O Ollama do computador não respondeu (é ele que gera os embeddings da busca). "
                         "Abra o app do Ollama, confira com: ollama list")
