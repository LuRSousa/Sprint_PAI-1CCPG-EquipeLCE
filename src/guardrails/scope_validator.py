import re
import unicodedata
from typing import List

from src.schemas.consulta_recarga import ConsultaSessoesSemana

TERMOS_ESCOPO = [
    "carregador",
    "carregadores",
    "eletroposto",
    "recarga",
    "recargas",
    "sessao",
    "sessoes",
    "potencia",
    "kw",
    "kwh",
    "demanda",
    "faturamento",
    "receita",
    "ticket",
    "tarifa",
    "ocpp",
    "modbus",
    "alerta",
    "alertas",
    "falha",
    "consumo",
    "pico",
    "manutencao",
    "posto",
    "energia",
    "chargegrid",
    "goodwe",
    "veiculo eletrico",
    "carro eletrico",
    "ev",
    "operacao",
    "conector",
    "heartbeat",
    "sobrecarga",
]

TERMOS_JURIDICO = [
    "processo judicial",
    "advogado",
    "contrato pode ser rescindido",
    "posso processar",
    "acao judicial",
    "clausula contratual",
    "multa contratual legal",
    "responsabilidade civil",
    "lgpd me obriga",
]

TERMOS_FINANCEIRO = [
    "investir",
    "investimento em acoes",
    "acoes da bolsa",
    "criptomoeda",
    "financiamento aprovado",
    "emprestimo",
    "declaracao de imposto",
    "sonegar",
    "planejamento tributario",
    "vale a pena comprar acoes",
]

TERMOS_SEGURANCA_ELETRICA = [
    "abrir o painel",
    "mexer na fiacao",
    "trocar o disjuntor",
    "religar o quadro",
    "fazer a ligacao eletrica",
    "aumentar o disjuntor",
    "burlar o limite de potencia",
    "sem desligar a energia",
    "desligar o aterramento",
    "gambiarra eletrica",
    "ponte no contator",
]

MENSAGEM_FORA_ESCOPO = (
    "Essa pergunta esta fora do escopo do ChargeGrid Assistant. "
    "Eu respondo sobre operacao do eletroposto: status dos carregadores, sessoes de recarga, "
    "potencia e demanda, alertas OCPP e faturamento. Posso ajudar em algum desses pontos?"
)

MENSAGEM_JURIDICO = (
    "Nao posso dar orientacao juridica. Esse ponto envolve interpretacao de contrato e legislacao, "
    "e precisa da avaliacao de um advogado ou do juridico da sua empresa. "
    "Posso, sim, levantar os dados operacionais do posto que embasem essa conversa."
)

MENSAGEM_FINANCEIRO = (
    "Nao posso dar recomendacao financeira ou de investimento. Decisoes desse tipo exigem um "
    "profissional habilitado (contador ou consultor financeiro registrado). "
    "O que posso fazer e apresentar os numeros de faturamento e consumo do posto."
)

MENSAGEM_SEGURANCA_ELETRICA = (
    "Nao posso orientar intervencao eletrica. Procedimentos em quadro, fiacao, protecao ou limite "
    "de potencia devem ser executados por eletricista ou engenheiro eletricista habilitado, "
    "seguindo a NR-10 e a norma do fabricante. "
    "Posso registrar o alerta e mostrar as leituras do carregador para o chamado tecnico."
)


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def _contem(texto: str, termos: List[str]) -> bool:
    return any(termo in texto for termo in termos)


def dentro_do_escopo(pergunta: str) -> bool:
    texto = normalizar(pergunta)
    if len(texto) < 4:
        return False
    return _contem(texto, TERMOS_ESCOPO)


def validar_escopo(pergunta: str) -> ConsultaSessoesSemana:
    texto = normalizar(pergunta)

    if _contem(texto, TERMOS_SEGURANCA_ELETRICA):
        return ConsultaSessoesSemana(
            bloqueada=True,
            categoria="seguranca_eletrica",
            motivo="pedido de orientacao para intervencao eletrica",
            mensagem_usuario=MENSAGEM_SEGURANCA_ELETRICA,
        )

    if _contem(texto, TERMOS_JURIDICO):
        return ConsultaSessoesSemana(
            bloqueada=True,
            categoria="juridico",
            motivo="pedido de aconselhamento juridico",
            mensagem_usuario=MENSAGEM_JURIDICO,
        )

    if _contem(texto, TERMOS_FINANCEIRO):
        return ConsultaSessoesSemana(
            bloqueada=True,
            categoria="financeiro",
            motivo="pedido de aconselhamento financeiro",
            mensagem_usuario=MENSAGEM_FINANCEIRO,
        )

    if not dentro_do_escopo(pergunta):
        return ConsultaSessoesSemana(
            bloqueada=True,
            categoria="fora_escopo",
            motivo="assunto sem relacao com a operacao do eletroposto",
            mensagem_usuario=MENSAGEM_FORA_ESCOPO,
        )

    return ConsultaSessoesSemana(bloqueada=False)


PADROES_ESPECIFICACAO = [
    r"especificac\w+ (?:tecnica|completa)s? d[oa] ",
    r"ficha tecnica d[oa] ",
    r"quantos amperes tem o modelo",
    r"qual o preco de tabela d[oa] ",
    r"manual d[oa] ",
]

MENSAGEM_SEM_BASE = (
    "Nao tenho essa especificacao na base do ChargeGrid e nao vou inventar numeros de produto. "
    "Os dados que tenho sao os de operacao do posto (leituras de potencia, sessoes, alertas e "
    "faturamento). Para especificacao de equipamento, consulte a documentacao oficial GoodWe."
)


def exige_especificacao_inexistente(pergunta: str) -> ConsultaSessoesSemana:
    texto = normalizar(pergunta)
    for padrao in PADROES_ESPECIFICACAO:
        if re.search(padrao, texto):
            return ConsultaSessoesSemana(
                bloqueada=True,
                categoria="especificacao_nao_disponivel",
                motivo="pedido de especificacao de produto ausente da base",
                mensagem_usuario=MENSAGEM_SEM_BASE,
            )
    return ConsultaSessoesSemana(bloqueada=False)
