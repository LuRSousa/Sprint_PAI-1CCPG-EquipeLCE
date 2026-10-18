import os
import html
import json
import uuid
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import time

# Sprint 4: o app fica em app/ e o código em src/. A pasta src/ entra no caminho de import
# antes de qualquer import do projeto (na Sprint 3 o app ficava dentro de src/).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chain.builder import processar_pergunta, llm  # noqa: E402
from rag.config import BUSCA, COLECAO, K, LIMIAR, VERSAO_PROMPT  # noqa: E402
from rag.vector_store import info_colecao  # noqa: E402


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
    .cg-fonte {
        background: #141a26;
        border-left: 3px solid #00c8ff;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 6px 0;
        font-size: 0.85rem;
        color: #b8c4d0;
    }
    .cg-fonte b { color: #e0e0e0; }
    /* Sprint 4: o expander de fontes no mesmo tema escuro do chat */
    div[data-testid="stExpander"] details {
        background: #10151f;
        border: 1px solid #00c8ff33;
        border-radius: 8px;
    }
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary p { color: #9fdcff !important; }
    div[data-testid="stExpander"] summary:hover p { color: #00c8ff !important; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #8fa3b5 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #0066cc, #0044aa);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
    section[data-testid="stSidebar"] { background-color: #0d1420; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)


def _init_chatbot():

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "mensagens_ui" not in st.session_state:
        st.session_state.mensagens_ui = []

        boas_vindas = (
            "Olá! Sou o **ChargeGrid Assistant**, seu assistente operacional "
            "de eletropostos GoodWe. ⚡\n\n"
            "Tenho acesso aos dados do seu posto — carregadores, potência, "
            "alertas e faturamento — e à base de conhecimento do ChargeGrid: "
            "manual do operador, especificações, tarifas, regimento de condomínio, "
            "perguntas frequentes e segurança. Toda resposta mostra de onde veio a informação.\n\n"
            "Como posso ajudar hoje?"
        )

        st.session_state.mensagens_ui.append(
            {
                "role": "assistant",
                "content": boas_vindas
            }
        )


def _renderizar_sidebar():
    dados_path = Path(__file__).resolve().parent.parent / "data" / "mock_data.json"
    with open(dados_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    with st.sidebar:
        st.markdown("## ⚡ Painel do Posto")

        modelo_atual = os.environ.get("OLLAMA_MODEL", "llama3.1")
        st.caption(f"🤖 Modelo: `{modelo_atual}`")
        nuvem = "ollama.com" in os.environ.get("OLLAMA_BASE_URL", "https://ollama.com")
        st.caption(f"🌐 Provedor: `{'Ollama Cloud' if nuvem else 'Ollama no computador'}`")
        st.markdown("---")

        # Sprint 4: estado da base de conhecimento (RAG)
        st.markdown("### 📚 Base de conhecimento")
        try:
            info = info_colecao()
            st.caption(f"Coleção `{COLECAO}`: {info['chunks']} trechos")
            if BUSCA == "vetorial":
                st.caption(f"Busca semântica: {K} trechos por pergunta, nota mínima {LIMIAR:.2f}")
            else:
                st.caption(f"Busca híbrida ({'intercalada' if BUSCA == 'intercalada' else 'RRF'}): semântica + "
                           f"palavra-chave, {K} trechos por pergunta (nota mínima {LIMIAR:.2f} ou 2+ palavras da pergunta)")
            st.caption(f"Prompt RAG `{VERSAO_PROMPT}` · embeddings `nomic-embed-text` (Ollama local)")
        except Exception:
            st.warning("Base ainda não indexada. Rode `python src/rag/ingestao.py` com o Ollama aberto.")
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

            st.session_state.session_id = str(uuid.uuid4())

            st.session_state.mensagens_ui = [
                {
                    "role": "assistant",
                    "content": "Olá! Como posso ajudar? ⚡"
                }
            ]

            st.rerun()

        if st.button("💾 Exportar Histórico", use_container_width=True):
            historico = st.session_state.get("mensagens_ui", [])

            if historico:
                st.download_button(
                    label="📥 Baixar JSON",
                    data=json.dumps(
                        historico,
                        ensure_ascii=False,
                        indent=2
                    ),
                    file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                )
            else:
                st.info("Nenhuma conversa registrada.")

        st.markdown("---")
        st.caption("ChargeGrid Assistant v3.0 (Sprint 4: RAG)\nEV Challenge 2026 — FIAP + GoodWe\nEquipe LCE | 1CCPG")


PERGUNTAS_RAPIDAS = [
    "Quais carregadores estão ativos agora?",
    "O carregador 2 está offline. O que eu faço?",
    "Quanto custa recarregar às 18h?",
    "Como está o faturamento do mês?",
    "Qual o melhor horário para manutenção?",
]


def _mostrar_fontes(msg):
    """Sprint 4: fontes da resposta, embaixo de cada mensagem do assistente."""
    fontes = msg.get("fontes") or []
    if msg.get("guardrail"):
        st.caption(f"🛡️ Resposta do guardrail: `{msg['guardrail']}` (a pergunta não chegou ao modelo ou a resposta foi filtrada)")
    if not fontes:
        if msg.get("classificacao") == "nao_estruturada":
            st.caption("📚 Nenhum trecho da base passou na busca: a resposta usou só os dados do posto.")
        return
    with st.expander(f"📚 Fontes ({len(fontes)})"):
        for fonte in fontes:
            if fonte.get("nota") is None:
                st.markdown(
                    f'<div class="cg-fonte"><b>{html.escape(fonte["documento"])}</b> · '
                    f'{html.escape(fonte["secao"])}</div>',
                    unsafe_allow_html=True,
                )
                continue
            texto = fonte["texto"].replace("\n", " ")
            if len(texto) > 420:
                texto = texto[:420].rsplit(" ", 1)[0] + "…"
            # Na busca híbrida, mostra quem achou o trecho: um trecho achado só pela palavra-chave
            # pode ter similaridade abaixo do limiar
            achado = f' · achado pela busca: {fonte["origem"]}' if BUSCA != "vetorial" and fonte.get("origem") else ""
            # html.escape: o texto vem de PDF, e um PDF não pode injetar HTML na tela
            st.markdown(
                f'<div class="cg-fonte"><b>{html.escape(fonte["documento"])}</b> · seção '
                f'{html.escape(fonte["secao"])} · p. {fonte["pagina"]} · similaridade {fonte["nota"]:.2f}{achado}'
                f'<br>{html.escape(texto)}</div>',
                unsafe_allow_html=True,
            )


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
                f'<div class="msg-user">👤 <strong>Operador</strong><br>{html.escape(msg["content"])}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="msg-bot">⚡ <strong>ChargeGrid Assistant</strong></div>',
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])
            _mostrar_fontes(msg)

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
            
            inicio = time.perf_counter() # Início do cronômetro para medir latência
            
            try:
                resultado = processar_pergunta(
                    mensagem_final,
                    st.session_state.session_id
                )
                
                fim = time.perf_counter()

                latencia = fim - inicio
                print(f"Latência: {latencia:.2f} -----")
                
                resposta = resultado["resposta"]
            except Exception as e:
                resultado = {}
                resposta = f"❌ Erro: {e}"
        st.session_state.mensagens_ui.append({
            "role": "assistant",
            "content": resposta,
            "fontes": resultado.get("fontes", []),
            "guardrail": resultado.get("guardrail"),
            "classificacao": resultado.get("classificacao"),
        })
        st.rerun()


if __name__ == "__main__":
    main()
    