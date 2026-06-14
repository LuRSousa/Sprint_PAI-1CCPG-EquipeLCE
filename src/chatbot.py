import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import ollama

# Carrega variáveis do arquivo .env
load_dotenv()


def _carregar_system_prompt() -> str:
    """Carrega o system prompt do arquivo prompts/system_prompt.md."""
    base = Path(__file__).resolve().parent.parent
    with open(base / "prompts" / "system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()


def _carregar_dados_mock() -> dict:
    """Carrega os dados mock operacionais do arquivo data/mock_data.json."""
    base = Path(__file__).resolve().parent.parent
    with open(base / "data" / "mock_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


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


class ChargeGridChatbot:
    """
    Chatbot operacional ChargeGrid usando Ollama (local ou nuvem).

    Funciona com:
        - Ollama local: rode `ollama serve` e depois `ollama pull llama3.1`
        - Ollama cloud: configure as variáveis no arquivo .env

    Variáveis de ambiente suportadas:
        - OLLAMA_HOST: URL do servidor (ex: https://api.ollama.com)
        - OLLAMA_MODEL: nome do modelo (padrão: llama3.1)
    """

    MODELO = "llama3.1"

    def __init__(self, modelo: str | None = None):
        self._modelo = modelo or os.environ.get("OLLAMA_MODEL", self.MODELO)
        self._system_prompt = _carregar_system_prompt()
        self._dados_mock = _carregar_dados_mock()

        # Configura o cliente Ollama (local ou nuvem)
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self._client = ollama.Client(host=host)

        # ⭐ CORREÇÃO 1: Inicia histórico com system prompt injetado
        self._historico: list[dict] = [
            {"role": "system", "content": self._system_prompt}
        ]
        self._historico_interno: list[dict] = []
        self._turno: int = 0

        self._verificar_ollama()

    def _verificar_ollama(self) -> None:
        """Verifica se o modelo solicitado está disponível no servidor Ollama."""
        try:
            resposta = self._client.list()
            if hasattr(resposta, 'models'):
                modelos = resposta.models
            else:
                modelos = resposta.get('models', [])
            modelos_disponiveis = [m.model for m in modelos]
            encontrado = any(self._modelo in m for m in modelos_disponiveis)
            if not encontrado:
                disponiveis = ", ".join(modelos_disponiveis) or "nenhum"
                raise RuntimeError(
                    f"Modelo '{self._modelo}' não encontrado no Ollama.\n"
                    f"Modelos disponíveis: {disponiveis}\n"
                    f"Para baixar: ollama pull {self._modelo}"
                )
        except Exception as e:
            if "Connection refused" in str(e) or "ConnectError" in str(e):
                raise RuntimeError(
                    "Ollama não está rodando.\n"
                    "Para execução local: inicie com 'ollama serve'\n"
                    "Para execução em nuvem: verifique OLLAMA_HOST no .env"
                ) from e
            raise

    def enviar_mensagem(self, mensagem_usuario: str) -> str:
        """Envia uma mensagem ao chatbot e retorna a resposta."""
        self._turno += 1

        mensagem_com_contexto = (
            f"{_formatar_contexto_operacional(self._dados_mock)}\n\n"
            f"Pergunta do operador: {mensagem_usuario}"
        )

        self._historico.append({"role": "user", "content": mensagem_com_contexto})

        # ⭐ CORREÇÃO 3: Usa o cliente configurado (nuvem ou local)
        resposta = self._client.chat(
            model=self._modelo,
            messages=self._historico,
            options={"temperature": 0.3, "num_predict": 1024},
        )

        texto = resposta.message.content

        self._historico.append({"role": "assistant", "content": texto})

        self._historico_interno.append({
            "turno": self._turno,
            "timestamp": datetime.now().isoformat(),
            "usuario": mensagem_usuario,
            "assistente": texto,
        })

        # ⭐ CORREÇÃO 5: Limita o histórico para evitar estouro de contexto
        MAX_MSGS = 20
        if len(self._historico) > MAX_MSGS + 1:
            system = self._historico[0]  # preserva o system prompt
            self._historico = [system] + self._historico[-MAX_MSGS:]

        if self._turno % 5 == 0:
            texto += (
                "\n\n---\n💡 *Posso fazer um resumo das informações que consultamos "
                "até agora, se preferir.*"
            )

        return texto

    def obter_historico(self) -> list[dict]:
        """Retorna o histórico interno da conversa atual."""
        return self._historico_interno

    def limpar_historico(self) -> None:
        """Limpa o histórico da conversa, mantendo apenas o system prompt."""
        self._historico = [{"role": "system", "content": self._system_prompt}]
        self._historico_interno = []
        self._turno = 0

    def exportar_historico_json(self, caminho: str) -> None:
        """Exporta o histórico da conversa para um arquivo JSON."""
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(self._historico_interno, f, ensure_ascii=False, indent=2)
        print(f"Histórico exportado para: {caminho}")