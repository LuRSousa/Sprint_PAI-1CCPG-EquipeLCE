# OBSERVAÇÕES

'''
1. PROBLEMA: Após a injeção do mock_data.json, o modelo passou a não corresponder o resultado esperado no teste 9 (Pergunta Ambígua)
'''

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser 
from langchain_classic.memory import ConversationTokenBufferMemory
# from langchain_classic.chains import ConversationChain

import ollama
from pathlib import Path
import json

from dotenv import load_dotenv
import os

load_dotenv()

model = os.getenv("OLLAMA_MODEL")
api_key = os.getenv("OLLAMA_API_KEY")

def _carregar_system_prompt() -> str:
    """Carrega o system prompt do arquivo prompts/system_prompt.md."""
    base = Path(__file__).resolve().parent.parent.parent
    with open(base / "prompts" / "system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()
    
    
def _carregar_dados_mock() -> str:
    """Carrega os dados mock operacionais do arquivo data/mock_data.json."""
    base = Path(__file__).resolve().parent.parent.parent
    with open(base / "data" / "mock_data.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
        
    return json.dumps(dados, ensure_ascii=False, indent=2)
# 1. Template: define estrutura e variáveis do prompt
prompt = ChatPromptTemplate.from_messages([
    
    ("system", _carregar_system_prompt()
     + "\n\n"
     + "Contexto_operacional>\n"
     + "{contexto}\n"
     ),
    
    ("placeholder", "{history}"),
    
    ("human", "Pergunta do operador: {pergunta}")
    
])

# 2. Modelo: conecta ao Ollama Cloud
llm = ChatOllama(
    model=model,
    base_url="https://ollama.com",
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
)

# 3. Parser: extrai só o texto da resposta
parser = StrOutputParser()

# 4. Composição da Chain    
chain = prompt | llm | parser

# 5. Declaração da Memória TokenBuffer
memoria_token = ConversationTokenBufferMemory(
    llm = llm,
    max_token_limit = 800,
    memory_key = "history",
    return_messages = True,
)

# TESTE: Invocar a chain com as variáveis do template
while True:

    pergunta = input("\nDigite sua pergunta (ou 'sair'): ")

    if pergunta.lower() == "sair":
        break

    # Recupera somente o histórico
    memoria = memoria_token.load_memory_variables({})
    history = memoria["history"]

    # Executa a chain
    resposta = chain.invoke({
        "contexto": _carregar_dados_mock(),
        "history": history,
        "pergunta": pergunta,
    })

    # Exibe resposta
    print("\nChargeGrid Assistant:")
    print(resposta)

    # Salva pergunta + resposta na memória
    memoria_token.save_context(
        {"pergunta": pergunta},
        {"resposta": resposta}
    )
    
    print(f"Mensagens no buffer: {len(memoria['history'])}")
    