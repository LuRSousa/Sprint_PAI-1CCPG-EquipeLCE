"""Avaliação da Sprint 4: roda o eval set numa iteração do assistente e dá as notas.

Na raiz do projeto, com o venv ativo e o Ollama aberto:

    python evals/avaliar.py --iteracao 1 --amostra 3   # teste rápido: 3 perguntas
    python evals/avaliar.py --iteracao 1               # eval completo (24 itens)
    python evals/avaliar.py --iteracao 1 --continuar   # retoma depois de erro ou limite de uso
    python evals/avaliar.py --iteracao 0 --sem-ragas   # só as verificações automáticas
    python evals/avaliar.py --comparativo              # só refaz o comparativo.md
    python evals/avaliar.py --iteracao 1 --reverificar # refaz as verificações com as respostas salvas
    python evals/avaliar.py --iteracao 1 --modelo gpt-oss:20b   # outro modelo (relatorio_modelos.md)

Iterações:
    0  Sprint 3, sem RAG (evals/sprint3_baseline.py)
    1  RAG + prompt v1 (busca vetorial)
    2  RAG + prompt v2 (busca vetorial)
    3  RAG + prompt v2 + busca híbrida (semântica + BM25 pela RRF, com a pergunta completada pela conversa e pelos dados)
    4  RAG + prompt v2 + busca intercalada (as mesmas duas buscas, com as vagas divididas entre elas)

Notas de cada item:
- comportamento: respondeu quando devia responder; recusou quando devia recusar;
- fatos: a resposta traz o que o gabarito pede (deve_conter) e nada do que proíbe (nao_deve_conter);
- cita fonte: a resposta tem "(Fonte: ...)";
- citação certa: cita um documento e uma seção que respondem a pergunta (fontes_esperadas),
  ou os dados operacionais, quando a resposta vem só deles;
- busca: algum trecho recuperado é de uma seção esperada (só nas iterações com RAG);
- RAGAS, só nos itens em que o assistente deve responder: faithfulness (cada afirmação da
  resposta se apoia no contexto que o modelo recebeu?) e answer relevancy (a resposta
  responde à pergunta?).

Saídas em evals/resultados/: iteracao_<n>.json (tudo, item a item), iteracao_<n>.md (resumo
e respostas) e comparativo.md (as iterações completas lado a lado). Com --amostra ou --ids,
os arquivos ganham o sufixo _amostra e ficam fora do comparativo. Com --modelo, ganham o nome do
modelo (iteracao_1_gpt-oss-20b.json) e entram no comparativo_modelos.md; o juiz do RAGAS não muda.
"""
import argparse
import asyncio
import contextlib
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import warnings
from datetime import datetime
from pathlib import Path

import langchain_classic  # noqa: F401 - ao ser importado, religa os avisos de API antiga do LangChain
from langchain_core._api.deprecation import LangChainDeprecationWarning

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

# Avisos de API antiga do LangChain (memória da Sprint 3): não mudam o resultado e poluem a saída do eval
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

EVAL_SET = RAIZ / "evals" / "eval_set_sprint4.json"
PASTA_RESULTADOS = RAIZ / "evals" / "resultados"

ITERACOES = {
    0: {"nome": "Sprint 3 (sem RAG)", "modo": "sprint3"},
    1: {"nome": "RAG + prompt v1", "modo": "rag", "prompt": "v1", "busca": "vetorial"},
    2: {"nome": "RAG + prompt v2", "modo": "rag", "prompt": "v2", "busca": "vetorial"},
    3: {"nome": "RAG + prompt v2 + busca híbrida", "modo": "rag", "prompt": "v2", "busca": "hibrida"},
    4: {"nome": "RAG + prompt v2 + busca intercalada", "modo": "rag", "prompt": "v2", "busca": "intercalada"},
}

# Palavra que identifica cada documento numa citação (pelo número do arquivo)
DOCUMENTOS = {
    "01": "manual do operador",
    "02": "especificacoes",
    "03": "chargeops",
    "04": "tabela tarifaria",
    "05": "regimento",
    "06": "perguntas frequentes",
    "07": "seguranca e emergencia",
}

# Itens que devem ser respondidos: "não respondeu" é a frase de recusa do prompt RAG, a da Sprint 3
# ou um "não tenho essa informação". Fica de fora "não está disponível", que aparece em resposta
# certa ("o carregador 2 não está disponível").
RE_NAO_RESPONDEU = re.compile(
    r"nao encontrei essa informacao|nao tenho dados carregados|fora do (meu )?escopo"
    r"|nao (tenho|possuo|disponho de) (essa |esta |essas |estas |a |as )?(informac|dados)"
    r"|nao ha (dados|informac)|nao consta(m)? (nos|entre os) dados|nao consigo (informar|responder|dizer)"
)
# Itens que devem ser recusados: qualquer forma de recusa (o que a resposta não pode dizer é
# conferido à parte, no nao_deve_conter)
RE_RECUSA = re.compile(
    r"nao encontrei|fora do (meu )?escopo|nao posso|so posso ajudar|so consigo ajudar|meu foco"
    r"|nao tenho (essa|esta|essas|estas|informac|acesso|dados)|nao ha informac|nao compartilho"
    r"|nao vou (seguir|revelar|compartilhar|ignorar)|nao consigo (ajudar|responder|revelar|compartilhar)"
    r"|nao (estou|fui) (preparad|configurad|programad|treinad)|nao disponho|sem acesso"
    r"|infelizmente|desculp|lamento"
)
RE_CITACAO = re.compile(r"fonte\s*:\s*([^)\n]*)")

TEMPO_MAXIMO_METRICA = 600  # segundos por métrica e por item


# ---------------------------------------------------------------- texto e verificações

def _norm(texto: str) -> str:
    """Texto comparável: minúsculas, sem acento, sem negrito do markdown, um espaço só e número sem
    separador de milhar. O modelo escreve "**2** e **4**", "40 kW" com espaço fino e "R$ 6 248,00"
    (espaço fino como separador de milhar); sem isso, o gabarito não casa com a resposta."""
    texto = unicodedata.normalize("NFKD", texto or "")  # também troca espaço fino e não separável por espaço
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"[*`]", "", texto)
    texto = re.sub(r"(?<=\d)[ .](?=\d{3}(?!\d))", "", texto)  # 6.248 / 6 248 -> 6248 (5.1 e 1,10 ficam)
    return re.sub(r"\s+", " ", texto)


def _padrao(termo: str) -> re.Pattern:
    """Termo do gabarito como regex: tolera espaço a mais ou a menos e não casa pedaço de número."""
    t = _norm(termo).strip()
    p = re.escape(t).replace(r"\ ", r"\s*")
    if t[:1].isdigit():
        p = r"(?<![\d.,])" + p
    elif t[:1].isalpha():
        p = r"(?<![a-z])" + p
    if t[-1:].isdigit():
        p += r"(?!\d)"
    return re.compile(p)


def _contem(texto_norm: str, termo: str) -> bool:
    return bool(_padrao(termo).search(texto_norm))


def _citacoes(texto_norm: str) -> list[str]:
    """Cada citação "(Fonte: ...)", separada por ";" quando junta mais de um documento."""
    partes = []
    for bloco in RE_CITACAO.findall(texto_norm):
        partes += [p.strip() for p in bloco.split(";") if p.strip()]
    return partes


def _secao_na_citacao(secao: str, citacao: str) -> bool:
    return bool(re.search(rf"(?<![\d.,]){re.escape(secao)}(?!\d|\.\d)", citacao))


def _numero_secao(secao: str) -> str:
    return (secao or "").split(" ")[0]


def _bate_secao(numero: str, esperado: str) -> bool:
    return numero == esperado or numero.startswith(esperado + ".")


def verificar(item: dict, resposta: str, guardrail, fontes: list[dict], com_rag: bool) -> dict:
    texto = _norm(resposta)
    bloqueado = guardrail is not None
    proibidos = [t for t in item["nao_deve_conter"] if _contem(texto, t)]
    v = {"proibidos_encontrados": proibidos}

    if item["esperado"] == "recusar":
        recusou = bloqueado or bool(RE_RECUSA.search(texto))
        v["comportamento"] = recusou and not proibidos
        return v

    vazia = not texto.strip()
    if vazia:
        v["resposta_vazia"] = True
    v["comportamento"] = not vazia and not bloqueado and not RE_NAO_RESPONDEU.search(texto)
    faltando = [grupo for grupo in item["deve_conter"] if not any(_contem(texto, t) for t in grupo)]
    v["fatos_faltando"] = [" / ".join(g) for g in faltando]
    v["fatos"] = not faltando and not proibidos

    citacoes = _citacoes(texto)
    v["cita_fonte"] = bool(citacoes)
    if item["fontes_esperadas"]:
        v["citacao_certa"] = any(
            DOCUMENTOS[arquivo] in c and _secao_na_citacao(secao, c)
            for arquivo, secao in item["fontes_esperadas"]
            for c in citacoes
        )
    else:
        v["citacao_certa"] = any("dados operacionais" in c for c in citacoes)

    if com_rag and item["fontes_esperadas"]:
        recuperadas = [(f["arquivo"][:2], _numero_secao(f["secao"])) for f in fontes
                       if str(f.get("arquivo", "")).lower().endswith(".pdf")]
        v["busca"] = any(
            arq == arquivo and _bate_secao(num, secao)
            for arquivo, secao in item["fontes_esperadas"]
            for arq, num in recuperadas
        )
    return v


# ---------------------------------------------------------------- erros que param o eval

# Sem conexão, a mensagem diz qual Ollama falhou: o do computador gera os embeddings (busca e
# answer relevancy); o Ollama Cloud roda o assistente e o juiz.
SEM_OLLAMA_LOCAL = ("O Ollama do computador não respondeu (é ele que gera os embeddings da busca). "
                    "Abra o app do Ollama, confira com: ollama list")
SEM_CONEXAO = {
    "assistente": "Não consegui falar com o Ollama Cloud (ollama.com), onde roda o assistente. Confira a internet.",
    "juiz": ("Não consegui falar com o Ollama: o juiz roda no Ollama Cloud e os embeddings da answer relevancy "
             "no Ollama do computador. Confira a internet e se o app do Ollama está aberto (ollama list)."),
}


def _erro_fatal(erro, onde: str):
    """Erros que não adianta repetir item a item: chave, limite de uso, sem conexão."""
    vistos = set()
    while erro is not None and id(erro) not in vistos:
        vistos.add(id(erro))
        status = getattr(erro, "status_code", None)
        texto = str(erro).lower()
        if status == 401 or "unauthorized" in texto:
            return "O Ollama Cloud recusou a chave (401). Confira a OLLAMA_API_KEY no .env."
        if status == 429 or any(s in texto for s in ("usage limit", "rate limit", "too many requests", "quota")):
            return "O Ollama Cloud recusou por limite de uso (429)."
        if isinstance(erro, ConnectionError) or "failed to connect" in texto or "connection refused" in texto:
            return SEM_CONEXAO[onde]
        erro = erro.__cause__ or erro.__context__
    return None


class EvalInterrompido(Exception):
    pass


# ---------------------------------------------------------------- assistente

def carregar_assistente(iteracao: int):
    """Importa o fluxo da iteração. A versão do prompt precisa estar no ambiente antes do import."""
    cfg = ITERACOES[iteracao]
    if cfg["modo"] == "sprint3":
        import sprint3_baseline as s3
        info = {"versao_prompt": "Sprint 3 (system_prompt_v2.md)", "modelo": os.getenv("OLLAMA_MODEL"),
                "temperature": s3.llm.temperature, "top_p": s3.llm.top_p, "num_predict": s3.llm.num_predict,
                "colecao": None, "k": None, "limiar": None}
        return s3.processar_pergunta, (lambda fontes: [s3.CONTEXTO]), info

    os.environ["RAG_PROMPT_VERSAO"] = cfg["prompt"]
    os.environ["RAG_BUSCA"] = cfg["busca"]
    from rag.config import BUSCA, COLECAO, K, LIMIAR, MODELO_EMBEDDING
    from rag.vector_store import info_colecao
    info_colecao(COLECAO)  # para logo se a coleção não existir (falta rodar a ingestão)
    from chain import builder

    def contextos(fontes):
        trechos = [
            f"[{f['documento']}, seção {f['secao']}, página {f['pagina']}]\n{f['texto']}"
            for f in fontes if f.get("texto")
        ]
        return trechos + [builder.dados_formatados]

    info = {"versao_prompt": cfg["prompt"], "modelo": builder.model, "temperature": builder.llm.temperature,
            "top_p": builder.llm.top_p, "num_predict": builder.llm.num_predict, "modelo_router": builder.model_router,
            "colecao": COLECAO, "k": K, "limiar": LIMIAR, "embedding": MODELO_EMBEDDING, "busca": BUSCA}
    return builder.processar_pergunta, contextos, info


def rodar_item(processar, contextos, item: dict, iteracao: int, com_rag: bool) -> dict:
    from langchain_core.callbacks import get_usage_metadata_callback

    sessao = f"eval-it{iteracao}-{item['id']}-{time.time_ns()}"
    for pergunta in item["turnos"]:
        inicio = time.perf_counter()
        with get_usage_metadata_callback() as uso, contextlib.redirect_stdout(io.StringIO()):
            r = processar(pergunta, sessao)
        latencia = time.perf_counter() - inicio
        if r.get("classificacao") == "erro":
            raise EvalInterrompido(SEM_OLLAMA_LOCAL)  # o builder só devolve "erro" quando a busca falha

    tokens = list(uso.usage_metadata.values())
    resultado = {
        "id": item["id"],
        "categoria": item["categoria"],
        "esperado": item["esperado"],
        "turnos": item["turnos"],
        "resposta": r["resposta"],
        "classificacao": r.get("classificacao"),
        "guardrail": r.get("guardrail"),
        "fontes": [{k: f.get(k) for k in ("documento", "secao", "pagina", "arquivo", "nota", "origem")}
                   for f in r.get("fontes", []) if f.get("texto")],
        "consulta_busca": r.get("consulta_busca") if r.get("consulta_busca") != item["turnos"][-1] else None,
        "contextos": contextos(r.get("fontes", [])),
        "latencia_s": round(latencia, 2),
        "tokens_entrada": sum(t.get("input_tokens", 0) for t in tokens),
        "tokens_saida": sum(t.get("output_tokens", 0) for t in tokens),
    }
    resultado["verificacoes"] = verificar(item, r["resposta"], r.get("guardrail"), r.get("fontes", []), com_rag)
    return resultado


def resultado_com_erro(item: dict, erro: Exception, com_rag: bool) -> dict:
    """Item que deu erro (ex.: o router devolveu um JSON quebrado): conta como falha e o eval segue."""
    return {
        "id": item["id"], "categoria": item["categoria"], "esperado": item["esperado"], "turnos": item["turnos"],
        "resposta": "", "classificacao": None, "guardrail": None, "fontes": [], "contextos": [],
        "latencia_s": 0.0, "tokens_entrada": 0, "tokens_saida": 0,
        "erro": f"{type(erro).__name__}: {str(erro)[:200]}",
        "verificacoes": verificar(item, "", None, [], com_rag),
        "ragas": {}, "ragas_erros": {m: f"{SEM_NOTA} (o assistente deu erro)" for m in METRICAS},
    }


# ---------------------------------------------------------------- RAGAS

METRICAS = ("faithfulness", "answer_relevancy")
CHAMADAS_POR_METRICA = {"faithfulness": 2, "answer_relevancy": 3}  # afirmações + veredito; 3 perguntas
SEM_NOTA = "sem nota"
MOTIVO_SEM_NOTA = {
    "faithfulness": "o juiz não achou afirmações para conferir",
    "answer_relevancy": "o juiz não conseguiu escrever perguntas a partir da resposta",
}


def metricas_pendentes(resultado: dict) -> list[str]:
    """Métricas que ainda faltam no item. Erro de execução volta a ser tentado no --continuar;
    "sem nota" (resposta sem nenhuma afirmação para conferir) não."""
    if resultado["esperado"] != "responder":
        return []
    notas = resultado.get("ragas", {})
    erros = resultado.get("ragas_erros", {})
    return [m for m in METRICAS if notas.get(m) is None and not erros.get(m, "").startswith(SEM_NOTA)]


async def pontuar_ragas(resultados: list[dict], itens: dict, salvar) -> None:
    from ragas_compat import criar_metricas, fechar_juizes

    metricas = dict(zip(METRICAS, criar_metricas()))
    try:
        await _pontuar_pendentes(resultados, itens, salvar, metricas)
    finally:
        await fechar_juizes(metricas.values())


async def _pontuar_pendentes(resultados: list[dict], itens: dict, salvar, metricas: dict) -> None:
    from ragas_compat import montar_amostra

    pendentes = [r for r in resultados if metricas_pendentes(r)]
    for i, r in enumerate(pendentes, 1):
        amostra = montar_amostra(
            pergunta=" ".join(r["turnos"]),
            resposta=r["resposta"],
            contextos=r["contextos"],
            referencia=itens[r["id"]]["referencia"],
        )
        notas = r.setdefault("ragas", {})
        erros = r.setdefault("ragas_erros", {})
        for nome in metricas_pendentes(r):
            erros.pop(nome, None)
            inicio = time.perf_counter()
            try:
                nota = await metricas[nome].single_turn_ascore(amostra, timeout=TEMPO_MAXIMO_METRICA)
            except Exception as erro:  # noqa: BLE001 - o eval segue com os outros itens
                fatal = _erro_fatal(erro, "juiz")
                if fatal:
                    salvar()
                    raise EvalInterrompido(fatal) from erro
                erros[nome] = f"{type(erro).__name__}: {str(erro)[:200]}"
                nota = None
            if nota is not None and math.isnan(nota):
                erros[nome] = f"{SEM_NOTA} ({MOTIVO_SEM_NOTA[nome]})"
                nota = None
            notas[nome] = None if nota is None else round(float(nota), 3)
            notas[f"{nome}_s"] = round(time.perf_counter() - inicio, 1)
            if nome == "faithfulness" and getattr(metricas[nome], "ultimo_detalhe", None):
                r["faithfulness_afirmacoes"] = metricas[nome].ultimo_detalhe
        if not erros:
            r.pop("ragas_erros")
        salvar()
        print(f"  RAGAS [{i}/{len(pendentes)}] {r['id']}: faithfulness {_fmt(notas.get('faithfulness'))}"
              f" | answer relevancy {_fmt(notas.get('answer_relevancy'))}")


# ---------------------------------------------------------------- resumo e relatórios

def _fmt(valor, casas=2):
    if valor is None:
        return "–"
    return f"{valor:.{casas}f}".replace(".", ",")


def _pct(ok, total):
    return f"{ok}/{total} ({round(100 * ok / total)}%)" if total else "–"


def _media(valores):
    valores = [v for v in valores if v is not None]
    return (sum(valores) / len(valores), len(valores)) if valores else (None, 0)


def resumir(resultados: list[dict]) -> dict:
    def contar(chave, filtro=lambda r: True):
        com = [r for r in resultados if filtro(r) and chave in r["verificacoes"]]
        return sum(bool(r["verificacoes"][chave]) for r in com), len(com)

    responder = lambda r: r["esperado"] == "responder"  # noqa: E731
    recusar = lambda r: r["esperado"] == "recusar"  # noqa: E731
    fid, n_fid = _media([r.get("ragas", {}).get("faithfulness") for r in resultados])
    # Recusa ("não encontrei...") não afirma nada sobre o posto, mas o juiz conta a própria recusa como
    # afirmação sem apoio. Esta segunda média mostra a faithfulness só do que o assistente respondeu.
    fid_dadas, n_fid_dadas = _media([r.get("ragas", {}).get("faithfulness") for r in resultados
                                     if r["verificacoes"].get("comportamento")])
    rel, n_rel = _media([r.get("ragas", {}).get("answer_relevancy") for r in resultados])
    lat, _ = _media([r["latencia_s"] for r in resultados])
    tok_e, _ = _media([r["tokens_entrada"] for r in resultados])
    tok_s, _ = _media([r["tokens_saida"] for r in resultados])
    return {
        "comportamento": contar("comportamento"),
        "respondeu": contar("comportamento", responder),
        "recusou": contar("comportamento", recusar),
        "fatos": contar("fatos"),
        "cita_fonte": contar("cita_fonte"),
        "citacao_certa": contar("citacao_certa"),
        "busca": contar("busca"),
        "faithfulness": (fid, n_fid),
        "faithfulness_respostas": (fid_dadas, n_fid_dadas),
        "answer_relevancy": (rel, n_rel),
        "latencia_media_s": lat,
        "tokens_entrada_medio": tok_e,
        "tokens_saida_medio": tok_s,
    }


LINHAS_RESUMO = [
    ("comportamento", "Comportamento certo (respondeu ou recusou)"),
    ("respondeu", "… respondeu o que devia responder"),
    ("recusou", "… recusou o que devia recusar"),
    ("fatos", "Fatos do gabarito na resposta"),
    ("cita_fonte", "Cita a fonte"),
    ("citacao_certa", "Cita o documento e a seção certos"),
    ("busca", "Busca trouxe uma seção esperada"),
]


def _valor_resumo(resumo, chave):
    if chave in ("faithfulness", "faithfulness_respostas", "answer_relevancy"):
        media, n = resumo.get(chave, (None, 0))
        return f"{_fmt(media)} (n={n})" if n else "–"
    if chave == "latencia_media_s":
        return f"{_fmt(resumo[chave], 1)} s" if resumo[chave] is not None else "–"
    if chave in ("tokens_entrada_medio", "tokens_saida_medio"):
        return f"{round(resumo[chave]):,}".replace(",", ".") if resumo[chave] is not None else "–"
    return _pct(*resumo[chave])


TODAS_AS_LINHAS = LINHAS_RESUMO + [
    ("faithfulness", "RAGAS faithfulness (média)"),
    ("faithfulness_respostas", "… só das respostas dadas (sem as recusas)"),
    ("answer_relevancy", "RAGAS answer relevancy (média)"),
    ("latencia_media_s", "Latência média por pergunta"),
    ("tokens_entrada_medio", "Tokens de entrada por pergunta (média)"),
    ("tokens_saida_medio", "Tokens de saída por pergunta (média)"),
]


def _marca(valor):
    return "–" if valor is None else ("✅" if valor else "❌")


def escrever_markdown(dados: dict, caminho: Path) -> None:
    resumo = dados["resumo"]
    info = dados["config"]
    linhas = [
        f"# Iteração {dados['iteracao']}: {dados['nome']}",
        "",
        f"Rodada em {dados['inicio']} · {len(dados['itens'])} de {dados['itens_no_eval_set']} itens do eval set"
        + (" · **parcial**" if dados["parcial"] else ""),
        "",
        f"- Modelo: `{info.get('modelo')}` (temperature {info.get('temperature'):g}) · prompt: {info.get('versao_prompt')}",
    ]
    if info.get("colecao"):
        linhas.append(f"- Base: coleção `{info['colecao']}`, busca {info.get('busca', 'vetorial')}, k = {info['k']}, "
                      f"limiar {info['limiar']}, embedding `{info.get('embedding')}`")
    else:
        linhas.append("- Sem base de conhecimento (o modelo só recebe o mock_data.json)")
    linhas.append(f"- Juiz do RAGAS: `{dados.get('juiz') or 'não rodou'}`")
    linhas += ["", "## Resumo", "", "| Métrica | Resultado |", "|---|---|"]
    linhas += [f"| {rotulo} | {_valor_resumo(resumo, chave)} |" for chave, rotulo in TODAS_AS_LINHAS]
    linhas += [
        "",
        "## Item a item",
        "",
        "| Item | Esperado | Comportamento | Fatos | Cita fonte | Citação certa | Busca | Faithfulness | Answer relevancy | Observação |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in dados["itens"]:
        v = r["verificacoes"]
        rg = r.get("ragas", {})
        obs = []
        if r.get("erro"):
            obs.append(f"erro: {r['erro']}")
        if v.get("resposta_vazia"):
            obs.append("resposta vazia")
        if r.get("guardrail"):
            obs.append(f"guardrail: {r['guardrail']}")
        if v.get("fatos_faltando"):
            obs.append("faltou: " + "; ".join(v["fatos_faltando"]))
        if v.get("proibidos_encontrados"):
            obs.append("disse: " + "; ".join(v["proibidos_encontrados"]))
        for nome, erro in r.get("ragas_erros", {}).items():
            obs.append(f"{nome}: {erro}")
        sem_apoio = [a for a in r.get("faithfulness_afirmacoes", []) if not a["apoiada"]]
        if sem_apoio:
            obs.append(f"{len(sem_apoio)} de {len(r['faithfulness_afirmacoes'])} afirmações sem apoio no contexto")
        obs = [o.replace("|", "\\|").replace("\n", " ") for o in obs]
        linhas.append(
            f"| {r['id']} | {r['esperado']} | {_marca(v.get('comportamento'))} | {_marca(v.get('fatos'))} "
            f"| {_marca(v.get('cita_fonte'))} | {_marca(v.get('citacao_certa'))} | {_marca(v.get('busca'))} "
            f"| {_fmt(rg.get('faithfulness'))} | {_fmt(rg.get('answer_relevancy'))} | {' · '.join(obs)} |"
        )
    linhas += ["", "## Respostas", ""]
    for r in dados["itens"]:
        fontes = "; ".join(f"{f['documento']}, {f['secao']} (nota {_fmt(f['nota'], 3)})" for f in r["fontes"])
        linhas += [
            "<details>",
            f"<summary><b>{r['id']}</b> · {r['turnos'][-1]}</summary>",
            "",
        ]
        if len(r["turnos"]) > 1:
            linhas += ["Conversa: " + " → ".join(r["turnos"]), ""]
        if r.get("consulta_busca"):
            linhas += [f"*Texto usado na busca:* {r['consulta_busca']}", ""]
        linhas += [
            r["resposta"].strip(),
            "",
            f"*Trechos usados:* {fontes or 'nenhum'} · *latência* {_fmt(r['latencia_s'], 1)} s",
            "",
        ]
        sem_apoio = [a for a in r.get("faithfulness_afirmacoes", []) if not a["apoiada"]]
        if sem_apoio:
            linhas += ["*Afirmações sem apoio no contexto, segundo o juiz do RAGAS:*", ""]
            linhas += [f"- {a['afirmacao']} — {a['motivo']}" for a in sem_apoio]
            linhas.append("")
        linhas += ["</details>", ""]
    caminho.write_text("\n".join(linhas), encoding="utf-8")


def escrever_comparativo() -> Path | None:
    completas = []
    for n in sorted(ITERACOES):
        caminho = PASTA_RESULTADOS / f"iteracao_{n}.json"
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if not dados.get("parcial"):
                completas.append(dados)
    if not completas:
        return None
    cabecalho = "| Métrica | " + " | ".join(f"{d['iteracao']}. {d['nome']}" for d in completas) + " |"
    linhas = [
        "# Comparativo das iterações",
        "",
        "Mesmo eval set (`evals/eval_set_sprint4.json`) em todas. Gerado por `python evals/avaliar.py`.",
        "",
        cabecalho,
        "|---|" + "---|" * len(completas),
    ]
    for chave, rotulo in TODAS_AS_LINHAS:
        linhas.append(f"| {rotulo} | " + " | ".join(_valor_resumo(resumir(d["itens"]), chave) for d in completas) + " |")
    linhas += ["", "## Item a item (comportamento · fatos)", "",
               "| Item | " + " | ".join(f"Iteração {d['iteracao']}" for d in completas) + " |",
               "|---|" + "---|" * len(completas)]
    ids = [r["id"] for r in completas[-1]["itens"]]
    for id_item in ids:
        celulas = []
        for d in completas:
            r = next((x for x in d["itens"] if x["id"] == id_item), None)
            if r is None:
                celulas.append("–")
                continue
            v = r["verificacoes"]
            celulas.append(f"{_marca(v.get('comportamento'))} {_marca(v.get('fatos')) if 'fatos' in v else ''}".strip())
        linhas.append(f"| {id_item} | " + " | ".join(celulas) + " |")
    caminho = PASTA_RESULTADOS / "comparativo.md"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def _slug(modelo: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", modelo.lower()).strip("-")


def escrever_comparativo_modelos() -> Path | None:
    """Mesma iteração com modelos diferentes (rodadas com --modelo), lado a lado."""
    linhas = ["# Comparativo de modelos", "",
              "Mesma iteração e mesmo eval set, trocando só o modelo que responde (`--modelo`). "
              "O router e o juiz do RAGAS são os mesmos em todas as colunas.", ""]
    algum = False
    for n in sorted(ITERACOES):
        rodadas = []
        for caminho in sorted(PASTA_RESULTADOS.glob(f"iteracao_{n}*.json")):
            if caminho.stem.endswith("_amostra"):
                continue
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if not dados.get("parcial"):
                rodadas.append(dados)
        if len(rodadas) < 2:
            continue
        algum = True
        linhas += [f"## Iteração {n}: {ITERACOES[n]['nome']}", "",
                   "| | " + " | ".join(f"`{d['config'].get('modelo')}`" for d in rodadas) + " |",
                   "|---|" + "---|" * len(rodadas)]
        for chave, rotulo in (("temperature", "temperature"), ("top_p", "top_p"),
                              ("num_predict", "max_tokens (num_predict)"), ("k", "k (trechos)")):
            linhas.append(f"| {rotulo} | " + " | ".join(str(d["config"].get(chave, "–")) for d in rodadas) + " |")
        for chave, rotulo in TODAS_AS_LINHAS:
            linhas.append(f"| {rotulo} | " + " | ".join(_valor_resumo(resumir(d["itens"]), chave) for d in rodadas) + " |")
        linhas.append("")
    if not algum:
        return None
    caminho = PASTA_RESULTADOS / "comparativo_modelos.md"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def reverificar(caminho_json: Path, caminho_md: Path, eval_set: list[dict], iteracao: int, com_comparativo: bool):
    """Refaz as verificações automáticas com as respostas já salvas, sem chamar nenhum modelo.
    Serve para quando o verificador melhora: as notas do RAGAS e as respostas continuam as mesmas."""
    if not caminho_json.exists():
        raise SystemExit(f"{caminho_json.name} não existe: rode a iteração primeiro.")
    dados = json.loads(caminho_json.read_text(encoding="utf-8"))
    por_id = {it["id"]: it for it in eval_set}
    com_rag = ITERACOES[iteracao]["modo"] == "rag"
    for r in dados["itens"]:
        if r["id"] in por_id:
            r["verificacoes"] = verificar(por_id[r["id"]], r["resposta"], r.get("guardrail"), r.get("fontes", []), com_rag)
    dados["resumo"] = resumir(dados["itens"])
    dados["reverificado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    caminho_json.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_markdown(dados, caminho_md)
    feitos = [caminho_md]
    if com_comparativo:
        feitos += [c for c in (escrever_comparativo(), escrever_comparativo_modelos()) if c]
    for chave, rotulo in TODAS_AS_LINHAS:
        print(f"{rotulo}: {_valor_resumo(dados['resumo'], chave)}")
    print("\nAtualizados: " + ", ".join(str(c.relative_to(RAIZ)) for c in feitos))


# ---------------------------------------------------------------- principal

def selecionar(itens: list[dict], amostra: int | None, ids: str | None) -> list[dict]:
    if ids:
        pedidos = [i.strip() for i in ids.split(",") if i.strip()]
        desconhecidos = sorted(set(pedidos) - {it["id"] for it in itens})
        if desconhecidos:
            raise SystemExit(f"Esses ids não estão no eval set: {', '.join(desconhecidos)}")
        return [it for it in itens if it["id"] in pedidos]
    if amostra:
        # Um item de cada categoria, na ordem do arquivo, até completar a amostra
        por_categoria: dict[str, list] = {}
        for it in itens:
            por_categoria.setdefault(it["categoria"], []).append(it)
        escolhidos, rodada = [], 0
        while len(escolhidos) < min(amostra, len(itens)):
            for lista in por_categoria.values():
                if rodada < len(lista) and len(escolhidos) < amostra:
                    escolhidos.append(lista[rodada])
            rodada += 1
        return sorted(escolhidos, key=itens.index)
    return itens


def main():
    parser = argparse.ArgumentParser(description="Eval da Sprint 4 (ChargeGrid Assistant)")
    parser.add_argument("--iteracao", type=int, choices=sorted(ITERACOES))
    parser.add_argument("--amostra", type=int, help="roda só N itens (um de cada categoria primeiro)")
    parser.add_argument("--ids", help="roda só esses itens, separados por vírgula (ex.: base-01,fora-01)")
    parser.add_argument("--sem-ragas", action="store_true", help="não chama o juiz do RAGAS")
    parser.add_argument("--continuar", action="store_true", help="aproveita os itens já feitos no arquivo de resultado")
    parser.add_argument("--comparativo", action="store_true", help="só refaz o comparativo.md")
    parser.add_argument("--reverificar", action="store_true",
                        help="refaz só as verificações automáticas com as respostas salvas (não chama modelo)")
    parser.add_argument("--modelo", help="outro modelo para o assistente (ex.: gpt-oss:20b); o juiz não muda")
    args = parser.parse_args()

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    if args.comparativo:
        caminhos = [c for c in (escrever_comparativo(), escrever_comparativo_modelos()) if c]
        print("Atualizados: " + ", ".join(str(c.relative_to(RAIZ)) for c in caminhos) if caminhos
              else "Nenhuma iteração completa em evals/resultados/.")
        return
    if args.iteracao is None:
        parser.error("informe --iteracao (" + ", ".join(map(str, sorted(ITERACOES))) + ")")

    eval_set = json.loads(EVAL_SET.read_text(encoding="utf-8"))["itens"]
    itens = selecionar(eval_set, args.amostra, args.ids)
    amostra = bool(args.amostra or args.ids)
    sufixo = (f"_{_slug(args.modelo)}" if args.modelo else "") + ("_amostra" if amostra else "")
    caminho_json = PASTA_RESULTADOS / f"iteracao_{args.iteracao}{sufixo}.json"
    caminho_md = PASTA_RESULTADOS / f"iteracao_{args.iteracao}{sufixo}.md"
    cfg = ITERACOES[args.iteracao]

    if args.reverificar:
        reverificar(caminho_json, caminho_md, eval_set, args.iteracao, com_comparativo=not amostra)
        return
    if args.modelo:
        os.environ["OLLAMA_MODEL"] = args.modelo  # o builder lê o modelo no import

    try:
        processar, contextos, info = carregar_assistente(args.iteracao)
    except RuntimeError as erro:          # coleção não existe
        raise SystemExit(str(erro))
    except ValueError as erro:            # versão de prompt que ainda não existe
        raise SystemExit(f"Não deu para montar a iteração {args.iteracao}: {erro}")

    anteriores = {}
    if args.continuar and caminho_json.exists():
        antigo = json.loads(caminho_json.read_text(encoding="utf-8"))
        mesma_config = all(antigo.get("config", {}).get(c) == info.get(c)
                           for c in ("versao_prompt", "modelo", "colecao", "busca"))
        if mesma_config:
            anteriores = {r["id"]: r for r in antigo["itens"] if not r.get("erro")}  # item com erro roda de novo
            print(f"Continuando {caminho_json.name}: {len(anteriores)} itens já respondidos.")
        else:
            print(f"Aviso: {caminho_json.name} foi feito com outra configuração; começando do zero.")
    elif caminho_json.exists():
        print(f"Aviso: {caminho_json.name} já existe e vai ser substituído (para retomar, use --continuar).")

    com_rag = cfg["modo"] == "rag"

    def chamadas_juiz(item):
        if args.sem_ragas:
            return 0
        if item["id"] in anteriores:
            pendentes = metricas_pendentes(anteriores[item["id"]])
        else:
            pendentes = METRICAS if item["esperado"] == "responder" else []
        return sum(CHAMADAS_POR_METRICA[m] for m in pendentes)

    chamadas = sum(len(it["turnos"]) * (2 if com_rag else 1) for it in itens if it["id"] not in anteriores)
    chamadas_ragas = sum(chamadas_juiz(it) for it in itens)
    print(f"Iteração {args.iteracao}: {cfg['nome']} | {len(itens)} itens"
          f" | chamadas ao Ollama Cloud: ~{chamadas} do assistente"
          + (f" + ~{chamadas_ragas} do juiz do RAGAS" if chamadas_ragas else ""))

    dados = {
        "iteracao": args.iteracao,
        "nome": cfg["nome"],
        "config": info,
        "juiz": None,
        "inicio": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "itens_no_eval_set": len(eval_set),
        "parcial": True,
        "itens": [],
    }

    def salvar():
        dados["resumo"] = resumir(dados["itens"])
        caminho_json.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    interrompido = None
    try:
        for i, item in enumerate(itens, 1):
            if item["id"] in anteriores:
                dados["itens"].append(anteriores[item["id"]])
                continue
            try:
                r = rodar_item(processar, contextos, item, args.iteracao, com_rag)
            except EvalInterrompido:
                raise
            except Exception as erro:  # noqa: BLE001 - um item com erro não derruba o eval inteiro
                fatal = _erro_fatal(erro, "assistente")
                if fatal:
                    raise EvalInterrompido(fatal) from erro
                r = resultado_com_erro(item, erro, com_rag)
            dados["itens"].append(r)
            salvar()
            v = r["verificacoes"]
            situacao = "ok" if v["comportamento"] and v.get("fatos", True) else "FALHOU"
            if r.get("erro"):
                situacao = f"ERRO ({r['erro']})"
            print(f"[{i}/{len(itens)}] {item['id']}: {situacao} ({r['latencia_s']:.1f} s)")

        if not args.sem_ragas:
            from ragas_compat import modelo_juiz
            dados["juiz"] = modelo_juiz()
            n = sum(bool(metricas_pendentes(r)) for r in dados["itens"])
            print(f"RAGAS: juiz {dados['juiz']}, {n} respostas para avaliar")
            asyncio.run(pontuar_ragas(dados["itens"], {it["id"]: it for it in eval_set}, salvar))
    except EvalInterrompido as erro:
        interrompido = str(erro)
    except KeyboardInterrupt:
        interrompido = "Interrompido no teclado (Ctrl+C)."

    # Itens do arquivo anterior que o laço não chegou a copiar (parada no meio) continuam no resultado
    feitos = {r["id"] for r in dados["itens"]}
    dados["itens"] += [anteriores[it["id"]] for it in itens if it["id"] in anteriores and it["id"] not in feitos]
    ordem = [it["id"] for it in eval_set]
    dados["itens"].sort(key=lambda r: ordem.index(r["id"]))

    dados["fim"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["parcial"] = bool(interrompido) or amostra or len(dados["itens"]) < len(eval_set)
    salvar()
    escrever_markdown(dados, caminho_md)
    atualizados = [caminho_md]
    if not amostra:
        if not args.modelo:
            atualizados.append(escrever_comparativo())
        atualizados.append(escrever_comparativo_modelos())

    print()
    for chave, rotulo in TODAS_AS_LINHAS:
        print(f"{rotulo}: {_valor_resumo(dados['resumo'], chave)}")
    print("\nResultados: " + ", ".join(str(c.relative_to(RAIZ)) for c in atualizados if c))
    if interrompido:
        print(f"\nO eval parou: {interrompido}\nO que já foi feito está salvo. Para seguir de onde parou:"
              f"\n  python evals/avaliar.py --iteracao {args.iteracao}"
              + (f" --modelo {args.modelo}" if args.modelo else "")
              + (f" --amostra {args.amostra}" if args.amostra else "")
              + (f" --ids {args.ids}" if args.ids else "")
              + (" --sem-ragas" if args.sem_ragas else "") + " --continuar")
        sys.exit(2)


if __name__ == "__main__":
    main()
