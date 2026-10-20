import re
import unicodedata
from typing import List

from guardrails.ResultadoGuardrail import ResultadoGuardrail  # Sprint 4: import a partir de src/, como o resto do projeto

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
    # Sprint 4: assuntos da base de conhecimento
    "manual", "faq", "especificacao", "especificacoes", "firmware",
    "chargeops", "ev chargeops", "painel", "display", "status", "offline", "ocioso", "indisponivel",
    "reiniciar", "reinicio", "chamado", "chamados", "tecnico", "limite", "limites", "ramal",
    "conectores", "ccs2", "chademo", "gb/t", "tipo 2", "cabo", "bateria", "wallbox", "plug-in",
    "tarifas", "tarifaria", "bandeira", "preco", "precos", "custa", "custo", "cobranca", "cobrado",
    "pagamento", "pagar", "pix", "cartao", "nfc", "qr code", "reembolso", "estorno", "contestar",
    "ociosidade", "projecao", "relatorio",
    "condominio", "regimento", "garagem", "vaga", "vagas", "reserva", "reservas", "morador", "sindico",
    "rateio", "seguranca", "emergencia", "incendio", "fogo", "fumaca", "choque", "bombeiros",
    "extintor", "alagamento", "nr-10", "nr10",
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
    "Essa pergunta está fora do escopo do ChargeGrid Assistant. "
    "Eu respondo sobre a operação do eletroposto: status dos carregadores, sessões de recarga, "
    "potência e demanda, alertas, faturamento, tarifas, procedimentos e segurança do posto, "
    "e o regimento de recarga em condomínio. Posso ajudar em algum desses pontos?"
)

MENSAGEM_JURIDICO = (
    "Não posso dar orientação jurídica. Esse ponto envolve interpretação de contrato e legislação, "
    "e precisa da avaliação de um advogado ou do jurídico da sua empresa. "
    "Posso, sim, levantar os dados operacionais do posto que embasem essa conversa."
)

MENSAGEM_FINANCEIRO = (
    "Não posso dar recomendação financeira ou de investimento. Decisões desse tipo exigem um "
    "profissional habilitado (contador ou consultor financeiro registrado). "
    "O que posso fazer é apresentar os números de faturamento e consumo do posto."
)

MENSAGEM_SEGURANCA_ELETRICA = (
    "Não posso orientar intervenção elétrica. Procedimentos em quadro, fiação, proteção ou limite "
    "de potência devem ser executados por eletricista ou engenheiro eletricista habilitado, "
    "seguindo a NR-10 e a norma do fabricante. "
    "Posso mostrar as leituras do carregador e os alertas para você abrir o chamado técnico."
)


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def _contem(texto: str, termos: List[str]) -> bool:
    # Sprint 4: compara palavra inteira. Antes era "termo in texto", e o termo "ev"
    # aparecia dentro de qualquer palavra ("descreve", "levar"), deixando quase tudo no escopo.
    return any(re.search(rf"(?<!\w){re.escape(termo)}(?!\w)", texto) for termo in termos)


def dentro_do_escopo(pergunta: str) -> bool:
    texto = normalizar(pergunta)
    if len(texto) < 4:
        return False
    return _contem(texto, TERMOS_ESCOPO)


def validar_escopo(pergunta: str, contexto_relevante: bool = False) -> ResultadoGuardrail:
    """Bloqueia pedidos de risco (elétrico, jurídico, financeiro) e perguntas fora do escopo.

    contexto_relevante (Sprint 4): a busca achou trecho relevante na base ou a pergunta continua
    uma conversa. Nesses casos, faltar palavra-chave não basta para recusar ("E o 4?",
    "como eu pago?"); quem decide se está fora do escopo é o prompt RAG (regra 5).
    """
    texto = normalizar(pergunta)

    if _contem(texto, TERMOS_SEGURANCA_ELETRICA):
        return ResultadoGuardrail(
            bloqueada=True,
            categoria="seguranca_eletrica",
            motivo="pedido de orientacao para intervencao eletrica",
            mensagem_usuario=MENSAGEM_SEGURANCA_ELETRICA,
        )

    if _contem(texto, TERMOS_JURIDICO):
        return ResultadoGuardrail(
            bloqueada=True,
            categoria="juridico",
            motivo="pedido de aconselhamento juridico",
            mensagem_usuario=MENSAGEM_JURIDICO,
        )

    if _contem(texto, TERMOS_FINANCEIRO):
        return ResultadoGuardrail(
            bloqueada=True,
            categoria="financeiro",
            motivo="pedido de aconselhamento financeiro",
            mensagem_usuario=MENSAGEM_FINANCEIRO,
        )

    if not dentro_do_escopo(pergunta) and not contexto_relevante:
        return ResultadoGuardrail(
            bloqueada=True,
            categoria="fora_escopo",
            motivo="assunto sem relacao com a operacao do eletroposto",
            mensagem_usuario=MENSAGEM_FORA_ESCOPO,
        )

    return ResultadoGuardrail(bloqueada=False)


PADROES_ESPECIFICACAO = [
    r"especificac\w+ (?:tecnica|completa)s? d[oa] ",
    r"ficha tecnica d[oa] ",
    r"quantos amperes tem o modelo",
    r"qual o preco de tabela d[oa] ",
    r"manual d[oa] ",
]

MENSAGEM_SEM_BASE = (
    "Não tenho essa especificação na base do ChargeGrid e não vou inventar números de produto. "
    "Para especificação de equipamento, consulte a documentação oficial do fabricante."
)


def exige_especificacao_inexistente(pergunta: str) -> ResultadoGuardrail:
    # Sprint 4: não é mais chamada. Com a base de manuais e especificações, bloquear
    # "manual do..." ou "ficha técnica do..." impediria justamente as perguntas que o RAG responde.
    # A recusa de especificação que não está na base passou para o prompt RAG (regra 3).
    texto = normalizar(pergunta)
    for padrao in PADROES_ESPECIFICACAO:
        if re.search(padrao, texto):
            return ResultadoGuardrail(
                bloqueada=True,
                categoria="especificacao_nao_disponivel",
                motivo="pedido de especificacao de produto ausente da base",
                mensagem_usuario=MENSAGEM_SEM_BASE,
            )
    return ResultadoGuardrail(bloqueada=False)
