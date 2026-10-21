"""Monta o texto usado na busca a partir da pergunta, da conversa e dos dados do posto.

Só a busca usa esse texto; o modelo continua recebendo a pergunta como o operador escreveu.
Três casos do eval mostraram que a pergunta sozinha não basta para achar o trecho certo:

1. Pergunta de continuação: "E no vale?" não diz que o assunto é preço do kWh. Quando já existe
   conversa e a pergunta começa com "E", tem até 3 palavras ou se refere à conversa ("dele", "isso"),
   a pergunta anterior do operador entra junto. Pergunta curta mas completa ("Quanto custa recarregar
   às 18h?") fica sozinha: até 20/10, toda pergunta de até 6 palavras puxava a anterior, e depois de
   "O carregador 2 está offline" a busca trazia os trechos de falha em vez da tabela tarifária.
2. Carregador com alerta: "o carregador 3 está com um alerta" não diz qual alerta. O tipo do alerta
   ativo (nos dados) entra na busca, e aí o procedimento certo do manual aparece.
3. Sessão citada pelo código: "quanto foi cobrado na SESS-004" não fala de tarifa. O horário de
   início, a energia e o valor da sessão (nos dados) entram na busca e puxam a tabela tarifária.

Regras simples, sem chamada extra ao modelo: não custam tokens nem latência. Uma alternativa
seria pedir ao LLM que reescrevesse a pergunta, ao custo de mais uma chamada por mensagem.
"""
import re
from datetime import datetime

MAX_PALAVRAS_CONTINUACAO = 3
# Palavras que só fazem sentido com a conversa ("qual o limite dele?", "isso é normal?")
REFERENCIAS_A_CONVERSA = {
    "ele", "ela", "eles", "elas", "dele", "dela", "deles", "delas", "nele", "nela",
    "isso", "disso", "nisso", "esse", "essa", "esses", "essas", "desse", "dessa", "nesse", "nessa",
    "aquele", "aquela", "aquilo", "daquele", "daquela", "mesmo", "mesma",
}


def _pergunta_anterior(historico) -> str | None:
    for mensagem in reversed(historico or []):
        if getattr(mensagem, "type", "") == "human":
            return mensagem.content
    return None


def _parece_continuacao(pergunta: str) -> bool:
    texto = pergunta.strip().lower()
    palavras = re.findall(r"\w+", texto)
    return (texto.startswith(("e ", "e,")) or len(palavras) <= MAX_PALAVRAS_CONTINUACAO
            or any(p in REFERENCIAS_A_CONVERSA for p in palavras))


def montar_consulta(pergunta: str, historico=None, dados: dict | None = None) -> str:
    partes = []
    anterior = _pergunta_anterior(historico)
    if anterior and _parece_continuacao(pergunta):
        partes.append(anterior)
    partes.append(pergunta)
    texto = " ".join(partes)

    if dados:
        citados = {int(n) for n in re.findall(r"carregador(?:es)?\s+(\d+)", texto, re.I)}
        for alerta in dados.get("alertas", []):
            if alerta["id_carregador"] in citados:
                partes.append(alerta["tipo"].replace("_", " "))

        for codigo in {c.upper() for c in re.findall(r"sess-\d+", texto, re.I)}:
            sessao = next((s for s in dados.get("sessoes_recarga", []) if s["id_sessao"] == codigo), None)
            if sessao:
                inicio = datetime.fromisoformat(sessao["inicio"])
                valor = f"R$ {sessao['valor_cobrado']:.2f}".replace(".", ",") if sessao.get("valor_cobrado") is not None else ""
                partes.append(f"sessão iniciada às {inicio:%H:%M} {str(sessao['energia_kwh']).replace('.', ',')} kWh {valor}")

    return " ".join(p for p in partes if p).strip()
