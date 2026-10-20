"""Teste da busca, sem LLM: que trechos o Chroma devolve para cada pergunta, e com que nota.

Serve para conferir se a recuperação acha a seção certa e para escolher o k e o limiar
de similaridade do retriever. Rode na raiz do projeto, com o Ollama aberto e depois da ingestão:
    python evals/teste_busca.py
O resultado também fica salvo em evals/resultados/teste_busca_<coleção>.md
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from rag.config import COLECAO  # noqa: E402
from rag.vector_store import buscar, info_colecao  # noqa: E402

# Pergunta e seções que respondem a ela: (início do nome do arquivo, número da seção)
NA_BASE = [
    ("O carregador 2 está offline. O que o operador deve fazer?", [("01", "5.1"), ("06", "2.1")]),
    ("Quanto custa recarregar às 18h?", [("04", "2"), ("06", "1.5")]),
    ("Qual é a potência máxima do carregador 3?", [("02", "3"), ("02", "2")]),
    ("Posso deixar o carro conectado a noite toda na garagem do condomínio?", [("05", "4.2"), ("05", "4.1")]),
    ("Por que a recarga fica mais lenta perto de 80%?", [("06", "1.3"), ("02", "5")]),
    ("Como é calculada a projeção de faturamento do mês?", [("03", "6.2")]),
    ("O que fazer se sair fumaça do carregador?", [("07", "4.1")]),
    ("Meu carro usa conector CHAdeMO. Consigo carregar no posto?", [("02", "6"), ("06", "1.2")]),
    ("O que é a taxa de ociosidade e quanto custa?", [("04", "5"), ("06", "1.6")]),
    ("Qual o melhor horário para fazer manutenção nos carregadores?", [("01", "7.3"), ("06", "2.3")]),
    ("O assistente consegue reiniciar um carregador?", [("06", "2.5"), ("01", "2.2")]),
    ("A sessão foi interrompida por falha do carregador. O cliente paga?", [("04", "6"), ("06", "1.7")]),
]
# Fora do domínio: o ideal é a nota do 1º trecho ficar baixa (é o que o limiar usa para recusar)
FORA_DO_DOMINIO = [
    "Qual é a capital da Austrália?",
    "Me passa uma receita de bolo de chocolate.",
    "Quem ganhou a Copa do Mundo de 2022?",
]
# Do domínio, mas a base não tem a resposta: a busca acha trechos parecidos, e quem recusa é o prompt
SEM_RESPOSTA_NA_BASE = [
    "Qual é o peso do carregador?",
    "Qual é a bandeira tarifária deste mês?",
]


def numero_da_secao(meta):
    return meta["secao"].split()[0]


def acertou(resultados, esperados):
    return any(
        meta["arquivo"].startswith(arq) and numero_da_secao(meta) == sec
        for meta in (doc.metadata for doc, _ in resultados)
        for arq, sec in esperados
    )


def rotulo(doc):
    meta = doc.metadata
    return f"{meta['arquivo'][:2]} {meta['documento']} | {meta['secao']} | p. {meta['pagina']}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--colecao", default=COLECAO)
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    info = info_colecao(args.colecao)
    linhas = [
        f"# Teste de busca: coleção `{args.colecao}`",
        "",
        f"- Data: {datetime.now():%d/%m/%Y %H:%M}",
        f"- Chunks na coleção: {info['chunks']} | chunk_size: {info.get('chunk_size', '?')} | "
        f"overlap: {info.get('chunk_overlap', '?')} | k: {args.k}",
        "",
        "## Perguntas que a base responde",
        "",
        "| # | Pergunta | Nota do 1º | Seção esperada no 1º? | No top-k? |",
        "|---|---|---|---|---|",
    ]
    detalhes = ["", "## Trechos devolvidos", ""]
    top1_base, acertos_1, acertos_k = [], 0, 0

    for i, (pergunta, esperados) in enumerate(NA_BASE, 1):
        res = buscar(pergunta, k=args.k, nome=args.colecao)
        a1, ak = acertou(res[:1], esperados), acertou(res, esperados)
        acertos_1 += a1
        acertos_k += ak
        top1_base.append(res[0][1])
        linhas.append(f"| {i} | {pergunta} | {res[0][1]:.3f} | {'sim' if a1 else 'não'} | {'sim' if ak else 'NÃO'} |")
        print(f"[{'ok' if ak else 'ERROU'}] {res[0][1]:.3f}  {pergunta}")
        detalhes.append(f"**{i}. {pergunta}**")
        detalhes += [f"- {nota:.3f} · {rotulo(doc)}" for doc, nota in res] + [""]

    def bloco(titulo, perguntas):
        notas = []
        linhas.extend(["", f"## {titulo}", "", "| Pergunta | Nota do 1º | 1º trecho |", "|---|---|---|"])
        for pergunta in perguntas:
            res = buscar(pergunta, k=args.k, nome=args.colecao)
            notas.append(res[0][1])
            linhas.append(f"| {pergunta} | {res[0][1]:.3f} | {rotulo(res[0][0])} |")
            print(f"[fora ] {res[0][1]:.3f}  {pergunta}")
        return notas

    top1_fora = bloco("Fora do domínio", FORA_DO_DOMINIO)
    top1_sem = bloco("Do domínio, sem resposta na base", SEM_RESPOSTA_NA_BASE)

    menor_base, maior_fora = min(top1_base), max(top1_fora)
    if menor_base > maior_fora:
        sugestao = (f"as notas separam bem: um limiar entre {maior_fora:.2f} e {menor_base:.2f} "
                    f"(ex.: {(menor_base + maior_fora) / 2:.2f}) recusa o que está fora do domínio")
    else:
        sugestao = ("as notas se sobrepõem: o limiar sozinho não separa, e a recusa depende "
                    "também do validador de escopo e do prompt")
    resumo = [
        "", "## Resumo", "",
        f"- Seção certa no 1º trecho: {acertos_1}/{len(NA_BASE)}",
        f"- Seção certa entre os {args.k} primeiros: {acertos_k}/{len(NA_BASE)}",
        f"- Menor nota do 1º trecho nas perguntas da base: {menor_base:.3f}",
        f"- Maior nota do 1º trecho fora do domínio: {maior_fora:.3f}",
        f"- Notas do 1º trecho sem resposta na base: {', '.join(f'{n:.3f}' for n in top1_sem)}",
        f"- Limiar: {sugestao}",
    ]

    destino = RAIZ / "evals" / "resultados" / f"teste_busca_{args.colecao}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas + resumo + detalhes) + "\n", encoding="utf-8")
    print("\n".join(resumo))
    print(f"\nResultado completo salvo em {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
