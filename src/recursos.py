from pathlib import Path
import json
import tiktoken
import calendar
from datetime import datetime

# Objeto encoder/tokenizer
enc = tiktoken.get_encoding("cl100k_base")

def _carregar_system_prompt() -> str:
    """Carrega o system prompt do arquivo prompts/system_prompt.md."""
    
    base = Path(__file__).resolve().parent.parent
    with open(base / "prompts" / "system_prompts" / "system_prompt_v2.md", "r", encoding="utf-8") as f:
        return f.read()

def _carregar_router_system_prompt() -> str:
    """Carrega o router system prompt do arquivo prompts/router_system_prompt.md."""
    
    base = Path(__file__).resolve().parent.parent
    with open(base / "prompts" / "router_system_prompts" / "router_system_prompt_v2.md", "r", encoding="utf-8") as f:
        return f.read()
    
    return 
    
def _carregar_dados_mock() -> dict:
    """Carrega os dados mock operacionais do arquivo data/mock_data.json."""
    base = Path(__file__).resolve().parent.parent
    with open(base / "data" / "mock_data.json", "r", encoding="utf-8") as f:
        return json.load(f)
        
    return json.dumps(dados, ensure_ascii=False, indent=2)

def _num(valor) -> str:
    """Número no formato brasileiro, sem casas decimais sobrando: 38.7 -> 38,7 ; 40.0 -> 40."""
    return f"{valor:g}".replace(".", ",")


def _reais(valor) -> str:
    """Valor em reais no formato brasileiro: 6248.0 -> R$ 6.248,00."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _data_referencia(dados: dict) -> datetime:
    """Data e hora da última leitura que aparece nos dados.

    A projeção e o cabeçalho usam essa data, e não a data de hoje: assim o mesmo
    conjunto de dados sempre gera os mesmos números (Guia EV ChargeOps, seção 6.2).
    """
    marcas = [s["inicio"] for s in dados["sessoes_recarga"]]
    marcas += [s["fim"] for s in dados["sessoes_recarga"] if s.get("fim")]
    marcas += [a["timestamp"] for a in dados["alertas"]]
    return max(datetime.fromisoformat(m) for m in marcas)


def _status_carregador(leitura: dict, alertas: list) -> str:
    """Mesma regra do Manual do Operador (seção 3.1): alerta crítico ativo vale mais que a potência."""
    critico = any(
        a["id_carregador"] == leitura["id_carregador"] and a["nivel"] == "critico" for a in alertas
    )
    if critico:
        return "EM FALHA (alerta crítico ativo)"
    if leitura["potencia_atual_kw"] > 0:
        return "EM RECARGA"
    return "DISPONÍVEL (ocioso)"


def _formatar_contexto_operacional(dados: dict) -> str:
    """Formata os dados mock em contexto estruturado para injeção no LLM."""
    referencia = _data_referencia(dados)
    sessoes_ativas = [s for s in dados["sessoes_recarga"] if s["status"] == "ativa"]
    sessoes_encerradas = [s for s in dados["sessoes_recarga"] if s["status"] != "ativa"]

    linhas_sessoes = [
        f"  - Carregador {s['id_carregador']}: sessão {s['id_sessao']}, "
        f"início {datetime.fromisoformat(s['inicio']):%d/%m/%Y %H:%M}, consumo até agora {_num(s['energia_kwh'])} kWh"
        for s in sessoes_ativas
    ] or ["  Nenhuma sessão ativa no momento."]

    linhas_encerradas = [
        f"  - {s['id_sessao']} (carregador {s['id_carregador']}): {s['status'].replace('_', ' ')}, "
        f"{_num(s['energia_kwh'])} kWh, valor cobrado {_reais(s['valor_cobrado'] or 0)}"
        for s in sessoes_encerradas
    ] or ["  Nenhuma sessão encerrada hoje."]

    linhas_potencia = [
        f"  - Carregador {p['id_carregador']}: {_num(p['potencia_atual_kw'])} kW "
        f"({p['percentual_uso']}% do limite de {_num(p['limite_kw'])} kW) — {_status_carregador(p, dados['alertas'])}"
        for p in dados["leituras_potencia"]
    ]

    linhas_alertas = [
        f"  - [{'CRÍTICO' if a['nivel'] == 'critico' else 'AVISO'}] {a['tipo']} — "
        f"carregador {a['id_carregador']} às {datetime.fromisoformat(a['timestamp']):%H:%M}: {a['descricao']}"
        for a in dados["alertas"]
    ] or ["  Nenhum alerta ativo."]

    fat = dados["faturamento"]
    fa, fp = fat["atual"], fat["anterior"]
    variacao = round(((fa["receita_total"] - fp["receita_total"]) / fp["receita_total"]) * 100, 1)
    dias_no_mes = calendar.monthrange(referencia.year, referencia.month)[1]
    projecao = round(fa["receita_total"] / referencia.day * dias_no_mes, 2)
    hist = dados["historico_demanda_semanal"]

    return f"""=== DADOS OPERACIONAIS DO POSTO — última leitura: {referencia:%d/%m/%Y %H:%M} ===

[SESSÕES ATIVAS — via OCPP]
{chr(10).join(linhas_sessoes)}

[SESSÕES ENCERRADAS HOJE]
{chr(10).join(linhas_encerradas)}

[LEITURAS DE POTÊNCIA — via MODBUS]
{chr(10).join(linhas_potencia)}

[ALERTAS DO SISTEMA]
{chr(10).join(linhas_alertas)}

[FATURAMENTO]
Mês atual ({fa['periodo']}, acumulado até {referencia:%d/%m}): {fa['total_sessoes']} sessões, {_num(fa['total_kwh'])} kWh, {_reais(fa['receita_total'])}
Ticket médio: {_reais(fa['ticket_medio'])} | Variação da receita vs {fp['periodo']} (mês fechado): {_num(variacao) if variacao <= 0 else '+' + _num(variacao)}%
Mês anterior ({fp['periodo']}): {fp['total_sessoes']} sessões, {_num(fp['total_kwh'])} kWh, {_reais(fp['receita_total'])}, ticket médio {_reais(fp['ticket_medio'])}
Projeção de fechamento: {_reais(projecao)} (receita acumulada ÷ {referencia.day} dias decorridos × {dias_no_mes} dias do mês)

[HISTÓRICO 7 DIAS]
Sessões: {hist['sessoes_total']} | Duração média: {hist['duracao_media_min']} min | Energia: {_num(hist['energia_total_kwh'])} kWh
Carregador mais usado: {hist['carregador_mais_usado']} ({hist['sessoes_carregador_mais_usado']} sessões)
Horários de pico: {', '.join(hist['horarios_pico'])} | Horários de vale: {', '.join(hist['horarios_vale'])} | Demanda no vale: {hist['percentual_demanda_vale']}%

=== FIM DOS DADOS ==="""


def contar_tokens_entrada(pergunta, history, dados_mock)->int:
    """Conta os tokens do histórico + contexto operacional + pergunta."""
    
    contexto = _formatar_contexto_operacional(dados_mock)

    texto_entrada = (
        f"{contexto}\n"
        f"{history}\n"
        f"Pergunta: {pergunta}"
    )

    return len(enc.encode(texto_entrada))
    