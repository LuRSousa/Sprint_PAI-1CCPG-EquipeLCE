from pathlib import Path
import json
import tiktoken
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
    
    
def _carregar_dados_mock() -> str:
    """Carrega os dados mock operacionais do arquivo data/mock_data.json."""
    
    base = Path(__file__).resolve().parent.parent
    with open(base / "data" / "mock_data.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
        
    return json.dumps(dados, ensure_ascii=False, indent=2)

def _formatar_contexto_operacional(dados: dict) -> str:
    """Formata os dados mock em contexto estruturado para injeção no LLM."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    sessoes_ativas = [s for s in dados["sessoes_recarga"] if s["status"] == "ativa"]
    sessoes_concluidas = [s for s in dados["sessoes_recarga"] if s["status"] == "concluída"]

    linhas_sessoes = [
        f"  - Carregador {s['id_carregador']}: sessão {s['id_sessao']}, "
        f"início {s['inicio']}, consumo atual {s['energia_kwh']} kWh"
        for s in sessoes_ativas
    ] or ["  Nenhuma sessão ativa no momento."]

    linhas_potencia = [
        f"  - Carregador {p['id_carregador']}: {p['potencia_atual_kw']} kW "
        f"({p['percentual_uso']}% do limite de {p['limite_kw']} kW) — "
        f"{'ATIVO' if p['potencia_atual_kw'] > 0 else 'OCIOSO'}"
        for p in dados["leituras_potencia"]
    ]

    linhas_alertas = [
        f"  - [{'CRÍTICO' if a['nivel'] == 'critico' else 'AVISO'}] "
        f"Carregador {a['id_carregador']} às {a['timestamp']}: {a['descricao']}"
        for a in dados["alertas"]
    ] or ["  Nenhum alerta ativo."]

    fat = dados["faturamento"]
    fa, fp = fat["atual"], fat["anterior"]
    variacao = round(((fa["receita_total"] - fp["receita_total"]) / fp["receita_total"]) * 100, 1)
    from datetime import date, timedelta
    hoje = date.today()
    dias_no_mes = (hoje.replace(day=28) + timedelta(days=4)).day
    projecao = round((fa["receita_total"] / max(hoje.day, 1)) * dias_no_mes, 2)
    hist = dados["historico_demanda_semanal"]

    return f"""=== DADOS OPERACIONAIS DO POSTO — {agora} ===

[SESSÕES ATIVAS — via OCPP]
{chr(10).join(linhas_sessoes)}
Sessões concluídas hoje: {len(sessoes_concluidas)}

[LEITURAS DE POTÊNCIA — via MODBUS]
{chr(10).join(linhas_potencia)}

[ALERTAS DO SISTEMA]
{chr(10).join(linhas_alertas)}

[FATURAMENTO]
Mês atual ({fa['periodo']}): {fa['total_sessoes']} sessões, {fa['total_kwh']} kWh, R$ {fa['receita_total']:,.2f}
Ticket médio: R$ {fa['ticket_medio']:,.2f} | Variação vs {fp['periodo']}: {'+' if variacao > 0 else ''}{variacao}%
Projeção fechamento: R$ {projecao:,.2f}

[HISTÓRICO 7 DIAS]
Sessões: {hist['sessoes_total']} | Duração média: {hist['duracao_media_min']} min | Energia: {hist['energia_total_kwh']} kWh
Carregador mais usado: {hist['carregador_mais_usado']} ({hist['sessoes_carregador_mais_usado']} sessões)
Picos: {', '.join(hist['horarios_pico'])} | Vale: {', '.join(hist['horarios_vale'])}

=== FIM DOS DADOS ===="""

def contar_tokens_entrada(history, pergunta, prompt)->int:
    '''Monta o prompt para retornar número tokens da entrada'''
    
    prompt_formatado = prompt.invoke({
        "contexto": _carregar_dados_mock(),
        "history": history,
        "pergunta": pergunta,
    })

    texto_entrada = "\n".join(
        mensagem.content
        for mensagem in prompt_formatado.messages
    )

    tokens_entrada = len(enc.encode(texto_entrada))
    
    return tokens_entrada
    