import re
from typing import List

# Sprint 4: imports a partir de src/, como o resto do projeto (antes "from src.guardrails...",
# que só funcionava rodando da raiz e fazia os guardrails nunca serem carregados pelo app)
from guardrails.scope_validator import normalizar, validar_escopo
from guardrails.ResultadoGuardrail import ResultadoGuardrail

PADROES_JAILBREAK: List[str] = [
    r"ignore (?:todas )?as (?:instrucoes|regras|orientacoes)",
    r"ignore (?:all )?(?:previous |prior )?instructions",
    r"esqueca (?:tudo|as regras|suas instrucoes|o que foi dito)",
    r"desconsidere (?:o|as|todas) (?:system prompt|instrucoes|regras)",
    r"a partir de agora voce (?:e|sera|vai ser)",
    r"finja que (?:voce )?(?:e|nao e|nao tem)",
    r"aja como se (?:voce )?nao tivesse",
    r"voce (?:esta|foi) (?:liberado|desbloqueado|sem restricoes)",
    r"modo (?:desenvolvedor|dev|debug|irrestrito|sem filtro)",
    r"developer mode",
    r"\bdan\b.{0,20}do anything now",
    r"jailbreak",
    r"sem (?:nenhum |qualquer )?filtro",
    r"responda (?:sem|ignorando) (?:as )?(?:regras|restricoes|limites)",
    r"nao precisa seguir (?:as )?regras",
]

PADROES_INJECAO: List[str] = [
    # Sprint 4: aceita mais de um artigo/possessivo ("mostre o seu prompt do sistema" passava)
    r"(?:mostre|revele|imprima|repita|exiba|me de|me mostre) (?:(?:o|a|os|as|seu|sua|seus|suas|todo|toda) )*"
    r"(?:system ?prompt|prompt do sistema|prompt inicial|instrucoes (?:internas|do sistema))",
    r"quais sao (?:as )?suas instrucoes",
    r"repita (?:tudo )?(?:o que|que) (?:esta|foi) (?:escrito )?(?:acima|antes|no inicio)",
    r"<\s*/?\s*(?:system|instrucoes|instructions|contexto_operacional)\s*>",
    r"\[\s*system\s*\]",
    r"###\s*(?:system|instruction)",
    r"new instructions?:",
    r"novas instrucoes:",
    r"override (?:the )?(?:system|rules)",
    r"execute (?:o )?(?:comando|codigo|script)",
    r"rm -rf",
    r"drop table",
    r"delete from",
    r"api[_ ]?key",
    r"variavel de ambiente",
]

MENSAGEM_JAILBREAK = (
    "Não vou seguir instruções que tentem alterar meu papel ou remover minhas regras. "
    "Eu sou o ChargeGrid Assistant e opero dentro do escopo do eletroposto. "
    "Se precisar de status de carregadores, sessões, demanda, alertas, faturamento ou "
    "procedimentos do posto, é só pedir."
)

MENSAGEM_INJECAO = (
    "Não compartilho minhas instruções internas nem executo comandos vindos do texto da conversa. "
    "Posso seguir ajudando com os dados e os procedimentos do posto."
)


def detectar_jailbreak(texto: str) -> bool:
    alvo = normalizar(texto)
    return any(re.search(padrao, alvo) for padrao in PADROES_JAILBREAK)


def detectar_injecao(texto: str) -> bool:
    alvo = normalizar(texto)
    return any(re.search(padrao, alvo) for padrao in PADROES_INJECAO)


def trecho_suspeito(texto: str) -> str | None:
    """Sprint 4: o pedaço do texto que bate com algum padrão de jailbreak ou injeção (ou None).

    Usado na ingestão para tirar do banco os trechos de documento com cara de instrução.
    """
    alvo = normalizar(texto)
    for padrao in PADROES_JAILBREAK + PADROES_INJECAO:
        achado = re.search(padrao, alvo)
        if achado:
            return achado.group(0)
    return None


def moderar(pergunta: str) -> ResultadoGuardrail:
    if detectar_jailbreak(pergunta):
        return ResultadoGuardrail(
            bloqueada=True,
            categoria="jailbreak",
            motivo="tentativa de sobrescrever o papel ou as regras do assistente",
            mensagem_usuario=MENSAGEM_JAILBREAK,
        )

    if detectar_injecao(pergunta):
        return ResultadoGuardrail(
            bloqueada=True,
            categoria="prompt_injection",
            motivo="tentativa de extrair instrucoes internas ou injetar comandos",
            mensagem_usuario=MENSAGEM_INJECAO,
        )

    return ResultadoGuardrail(bloqueada=False)


def aplicar_guardrails(pergunta: str, contexto_relevante: bool = False) -> ResultadoGuardrail:
    """Guardrails de entrada: jailbreak e injeção primeiro, depois o escopo.

    Sprint 4: saiu a checagem de especificação por palavra-chave ("manual do...", "ficha técnica
    do..."), que bloquearia as perguntas que a base agora responde. Quem recusa especificação
    que não está na base é o prompt RAG (regra 3).
    """
    resultado = moderar(pergunta)
    if resultado.bloqueada:
        return resultado

    return validar_escopo(pergunta, contexto_relevante=contexto_relevante)


PADROES_SAIDA_SUSPEITA = [
    r"system ?prompt",
    r"minhas instrucoes internas sao",
    r"api[_ ]?key",
    # Sprint 4: pedaços do prompt RAG que nunca deveriam aparecer numa resposta
    r"<\s*/?\s*(?:system_prompt|regras|identidade|fontes_de_informacao|exemplo_de_formato)\b",
    r"rag-v\d",
]

MENSAGEM_SAIDA_FILTRADA = (
    "Detectei conteúdo interno na resposta gerada e preferi não exibi-la. "
    "Pode reformular a pergunta sobre a operação do posto?"
)


def filtrar_saida(resposta: str) -> ResultadoGuardrail:
    alvo = normalizar(resposta)
    for padrao in PADROES_SAIDA_SUSPEITA:
        if re.search(padrao, alvo):
            return ResultadoGuardrail(
                bloqueada=True,
                categoria="vazamento_saida",
                motivo="resposta continha referencia a instrucoes internas",
                mensagem_usuario=MENSAGEM_SAIDA_FILTRADA,
            )
    return ResultadoGuardrail(bloqueada=False)
