import re
from typing import List

from src.guardrails.scope_validator import (
    exige_especificacao_inexistente,
    normalizar,
    validar_escopo,
)
from src.guardrails.ResultadoGuardrail import ResultadoGuardrail

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
    r"(?:mostre|revele|imprima|repita|exiba|me de) (?:o |seu |todo o )?(?:system ?prompt|prompt do sistema|prompt inicial)",
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
    "Nao vou seguir instrucoes que tentem alterar meu papel ou remover minhas regras. "
    "Eu sou o ChargeGrid Assistant e opero dentro do escopo do eletroposto. "
    "Se precisar de status de carregadores, sessoes, demanda, alertas ou faturamento, e so pedir."
)

MENSAGEM_INJECAO = (
    "Nao compartilho minhas instrucoes internas nem executo comandos vindos do texto da conversa. "
    "Posso seguir ajudando com os dados operacionais do posto."
)


def detectar_jailbreak(texto: str) -> bool:
    alvo = normalizar(texto)
    return any(re.search(padrao, alvo) for padrao in PADROES_JAILBREAK)


def detectar_injecao(texto: str) -> bool:
    alvo = normalizar(texto)
    return any(re.search(padrao, alvo) for padrao in PADROES_INJECAO)


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


def aplicar_guardrails(pergunta: str) -> ResultadoGuardrail:
    resultado = moderar(pergunta)
    if resultado.bloqueada:
        return resultado

    resultado = exige_especificacao_inexistente(pergunta)
    if resultado.bloqueada:
        return resultado

    return validar_escopo(pergunta)


PADROES_SAIDA_SUSPEITA = [
    r"system ?prompt",
    r"minhas instrucoes internas sao",
    r"api[_ ]?key",
]

MENSAGEM_SAIDA_FILTRADA = (
    "Detectei conteudo interno na resposta gerada e preferi nao exibi-la. "
    "Pode reformular a pergunta sobre a operacao do posto?"
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
