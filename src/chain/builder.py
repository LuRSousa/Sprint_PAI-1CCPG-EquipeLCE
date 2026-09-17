# OBSERVAÇÕES

'''
1. PROBLEMA: Após a injeção do mock_data.json, o modelo passou a não corresponder o resultado esperado no teste 9 (Pergunta Ambígua)
2. PROBLEMA: A llm porder perder o contexto do primeiro turno de conversa após poucos turnos depenendo da saída que ela produz (relatórios de anomalias, por exemplo, consomem muitos tokens)
'''

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser 
from memoria import criar_memoria, obter_historico, salvar_turno
# from langchain_classic.chains import ConversationChain

from pathlib import Path
import json

from dotenv import load_dotenv
import os

from router import classificar_prompt
from structured_builder import executar_chain_estruturada
from recursos import _carregar_system_prompt, _carregar_dados_mock

load_dotenv()

model = os.getenv("OLLAMA_MODEL")
api_key = os.getenv("OLLAMA_API_KEY")

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

# 5. Cria memória conversacional
memoria_token = criar_memoria(llm)

# TESTE: Invocar a chain com as variáveis do template
while True:

    pergunta = input("\nDigite sua pergunta (ou 'sair'): ")

    classificacao = classificar_prompt(llm, pergunta)

    print(f"\nPergunta: {pergunta}")
    print(f"Rota escolhida: {classificacao}")

    if pergunta.lower() == "sair":
        break
     
    
    elif classificacao == "nao_estruturada":
        
        # Recupera somente o histórico
        history = obter_historico(memoria_token)

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
        salvar_turno(memoria_token, pergunta, resposta)
        
        print(f"Mensagens no buffer: {len(obter_historico(memoria_token))}")
        # print(memoria)
    
    elif classificacao == "estruturada":
        
        history = obter_historico(memoria_token)
        resposta = executar_chain_estruturada(history, pergunta)
        # Exibe resposta
        print("\nChargeGrid Assistant:")
        print(resposta)

        # Salva pergunta + resposta na memória
        salvar_turno(memoria_token, pergunta, resposta)
        
        print(f"Mensagens no buffer: {len(obter_historico(memoria_token))}")
        # print(memoria)