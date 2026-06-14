import os
import json
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chatbot import ChargeGridChatbot


st.set_page_config(
    page_title="ChargeGrid Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #e0e0e0; }
    .cg-header {
        background: linear-gradient(135deg, #1a1f2e 0%, #0d2137 100%);
        border: 1px solid #00c8ff33;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 20px;
    }
    .cg-header h1 { color: #00c8ff; font-size: 1.7rem; margin: 0; }
    .cg-header p  { color: #8899aa; font-size: 0.85rem; margin: 4px 0 0 0; }
    .msg-user {
        background: #1e3a5f;
        border-radius: 12px 12px 2px 12px;
        padding: 12px 16px;
        margin: 8px 0 8px 15%;
        color: #d0e8ff;
        border-left: 3px solid #00c8ff;
    }
    .msg-bot {
        background: #1a1f2e;
        border-radius: 12px 12px 12px 2px;
        padding: 12px 16px;
        margin: 8px 15% 8px 0;
        color: #e0e0e0;
        border-left: 3px solid #22c55e;
    }
    .stTextInput > div > div > input {
        background-color: #1a1f2e !important;
        color: #e0e0e0 !important;
        border: 1px solid #00c8ff44 !important;
        border-radius: 8px !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0066cc, #0044aa);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
    section[data-testid="stSidebar"] { background-color: #0d1420; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)


def _init_chatbot():
    if "chatbot" not in st.session_state:
        # ⭐ CORREÇÃO 2: Variável de ambiente corrigida
        modelo = os.environ.get("OLLAMA_MODEL", "llama3.1")
        try:
            st.session_state.chatbot = ChargeGridChatbot(modelo=modelo)
            st.session_state.mensagens_ui = []
            boas_vindas = (
                "Olá! Sou o **ChargeGrid Assistant**, seu assistente operacional "
                "de eletropostos GoodWe. ⚡\n\n"
                "Tenho acesso aos dados do seu posto — carregadores, potência, "
                "alertas e faturamento.\n\nComo posso ajudar hoje?"
            )
            st.session_state.mensagens_ui.append({"role": "assistant", "content": boas_vindas})
        except RuntimeError as e:
            st.error(f"### ⚠️ Erro ao iniciar o Ollama\n\n```\n{e}\n```")
            st.info(
                "**Para resolver:**\n\n"
                "**Modo local:**\n"
                "1. Instale o Ollama: https://ollama.com/download\n"
                "2. No terminal, rode: `ollama serve`\n"
                "3. Baixe o modelo: `ollama pull llama3.1`\n\n"
                "**Modo nuvem:**\n"
                "1. Configure o arquivo `.env` com OLLAMA_HOST e sua API key\n"
                "2. Recarregue esta página"
            )
            st.stop()


def _renderizar_sidebar():
    dados_path = Path(__file__).resolve().parent.parent / "data" / "mock_data.json"
    with open(dados_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    with st.sidebar:
        st.markdown("## ⚡ Painel do Posto")

        modelo_atual = os.environ.get("OLLAMA_MODEL", "llama3.1")
        host_atual = os.environ.get("OLLAMA_HOST", "localhost")
        st.caption(f"🤖 Modelo: `{modelo_atual}`")
        st.caption(f"🌐 Host: `{host_atual}`")
        st.markdown("---")

        st.markdown("### 🔌 Carregadores")
        for p in dados["leituras_potencia"]:
            tem_critico = any(
                a["id_carregador"] == p["id_carregador"] and a["nivel"] == "critico"
                for a in dados["alertas"]
            )
            if p["potencia_atual_kw"] > 0:
                cor, label = "🟢", f"{p['potencia_atual_kw']} kW ({p['percentual_uso']}%)"
            elif tem_critico:
                cor, label = "🔴", "FALHA"
            else:
                cor, label = "⚫", "Ocioso"
            st.markdown(f"{cor} **Carregador {p['id_carregador']}** — {label}")

        st.markdown("---")
        st.markdown("### 🚨 Alertas")
        if dados["alertas"]:
            for a in dados["alertas"]:
                if a["nivel"] == "critico":
                    st.error(f"🔴 Carregador {a['id_carregador']} — {a['tipo'].replace('_',' ').title()}")
                else:
                    st.warning(f"🟡 Carregador {a['id_carregador']} — {a['tipo'].replace('_',' ').title()}")
        else:
            st.success("Nenhum alerta ativo")

        st.markdown("---")
        fat = dados["faturamento"]["atual"]
        st.markdown("### 💰 Faturamento — Maio/2026")
        st.metric("Receita", f"R$ {fat['receita_total']:,.2f}", "+6.1% vs abril")
        st.metric("Sessões", str(fat["total_sessoes"]))
        st.metric("Energia", f"{fat['total_kwh']} kWh")

        st.markdown("---")
        st.markdown("### ⚙️ Controles")

        if st.button("🗑️ Nova Conversa", use_container_width=True):
            st.session_state.chatbot.limpar_historico()
            st.session_state.mensagens_ui = [{"role": "assistant", "content": "Olá! Como posso ajudar? ⚡"}]
            st.rerun()

        if st.button("💾 Exportar Histórico", use_container_width=True):
            historico = st.session_state.chatbot.obter_historico()
            if historico:
                st.download_button(
                    label="📥 Baixar JSON",
                    data=json.dumps(historico, ensure_ascii=False, indent=2),
                    file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                )
            else:
                st.info("Nenhuma conversa registrada.")

        st.markdown("---")
        st.caption("ChargeGrid Assistant v2.0\nEV Challenge 2026 — FIAP + GoodWe\nEquipe LCE | 1CCPG")


PERGUNTAS_RAPIDAS = [
    "Quais carregadores estão ativos agora?",
    "Algum carregador está perto do limite?",
    "Teve alguma anomalia hoje?",
    "Como está o faturamento do mês?",
    "Melhor horário para manutenção?",
]


def main():
    _init_chatbot()
    _renderizar_sidebar()

    st.markdown("""
    <div class="cg-header">
        <h1>⚡ ChargeGrid Assistant</h1>
        <p>EV Challenge 2026 · FIAP + GoodWe · Trilha ChargeGrid Intelligence · Equipe LCE — 1CCPG</p>
    </div>
    """, unsafe_allow_html=True)

    # Perguntas rápidas
    st.markdown("**💬 Perguntas rápidas:**")
    cols = st.columns(len(PERGUNTAS_RAPIDAS))
    pergunta_rapida = None
    for i, perg in enumerate(PERGUNTAS_RAPIDAS):
        with cols[i]:
            label = perg[:26] + "…" if len(perg) > 26 else perg
            if st.button(label, key=f"q{i}", use_container_width=True):
                pergunta_rapida = perg

    st.markdown("---")

    # Histórico do chat
    for msg in st.session_state.mensagens_ui:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user">👤 <strong>Operador</strong><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="msg-bot">⚡ <strong>ChargeGrid Assistant</strong></div>',
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])

    st.markdown("---")

    # Input
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            label="msg",
            placeholder="Digite sua pergunta sobre o posto...",
            label_visibility="collapsed",
            key="user_input_field",
        )
    with col_btn:
        enviar = st.button("Enviar ➤", use_container_width=True)

    mensagem_final = pergunta_rapida or (user_input if enviar and user_input.strip() else None)

    if mensagem_final:
        st.session_state.mensagens_ui.append({"role": "user", "content": mensagem_final})
        with st.spinner("⚡ Consultando dados do posto..."):
            try:
                resposta = st.session_state.chatbot.enviar_mensagem(mensagem_final)
            except Exception as e:
                resposta = f"❌ Erro: {e}"
        st.session_state.mensagens_ui.append({"role": "assistant", "content": resposta})
        st.rerun()


if __name__ == "__main__":
    main()