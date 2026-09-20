# OBSERVAÇÕES

'''
PROBLEMAS: 

1. PROBLEMA: Após a injeção do mock_data.json, o modelo passou a não corresponder o resultado esperado no teste 9 
   (Pergunta Ambígua)
2. PROBLEMA: A llm porder perder o contexto do primeiro turno de conversa após poucos turnos depenendo da saída 
   que ela produz  (relatórios de anomalias, por exemplo, consomem muitos tokens)
3. PROBLEMA: O prompt v1 do router direciona (ás vezes) a resposta de "Alguma anomalia foi registrada essa semana?"
   para a chain estruturada (devia ser nao_estruturada). Já retornou a respota correta, mas fora do schema e já 
   retornou a resposta estruturada que não responde à pergunta Melhorar prompt v1

'''
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser 
from memoria import criar_memoria, obter_historico, salvar_turno
# from langchain_classic.chains import ConversationChain

from dotenv import load_dotenv
import os

from router import classificar_prompt
from structured_builder import executar_chain_estruturada
from recursos import _carregar_system_prompt, _carregar_dados_mock, contar_tokens_entrada

import time
import tiktoken

# Objeto encoder/tokenizer
enc = tiktoken.get_encoding("cl100k_base")

load_dotenv()

model = os.getenv("OLLAMA_MODEL")
model_router = os.getenv("OLLAMA_MODEL_ROUTER")
api_key = os.getenv("OLLAMA_API_KEY")
    
# Dados do mock
dados_mock = _carregar_dados_mock()

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

# 2. Conexões do modelo principal e de classificação de user prompt ao Ollama Cloud
llm = ChatOllama(
    
    model=model,
    base_url="https://ollama.com",
    num_predict=1024,
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
)

llm_router = ChatOllama(
    
    model=model_router,
    base_url="https://ollama.com",
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
)

# 3. Parser: extrai só o texto da resposta
parser = StrOutputParser()

# 4. Composição da Chain conversacional
chain = prompt | llm | parser

# 5. Cria memória conversacional
memoria_token = criar_memoria(llm)
history = memoria_token.load_memory_variables({})["history"] # string

# TESTE: Invocar a chain com as variáveis do template
while True:

    pergunta = input("\nDigite sua pergunta (ou 'sair'): ")
    
    inicio_router = time.perf_counter()
    
    classificacao = classificar_prompt(llm_router, pergunta)

    latencia_router = time.perf_counter() - inicio_router

    print(f"\nPergunta: {pergunta}") # !! Monitoramento
    print(f"Rota escolhida: {classificacao}") # !! Monitoramento

    if pergunta.lower() == "sair":

        break

    elif classificacao == "nao_estruturada": # executa chain conversacional

        # Recupera somente o histórico
        history = obter_historico(memoria_token) 
        
        tokens_entrada = contar_tokens_entrada(history, pergunta, dados_mock)
        inicio_resposta = time.perf_counter()
        
        # Executa a chain
        resposta = chain.invoke({ # Manda system prompt, contexto, histórico e pergunta ao modelo

            "contexto": _carregar_dados_mock(),
            "history": history,
            "pergunta": pergunta,

        })
        
        latencia_resposta = time.perf_counter() - inicio_resposta
        latencia_total = latencia_router + latencia_resposta
        
        tokens_saida = len(enc.encode(resposta))
        
        # Exibe resposta
        print("\nChargeGrid Assistant:")
        print(resposta) # !! Monitoramento

        # Salva pergunta + resposta na memória
        salvar_turno(memoria_token, pergunta, resposta)

        print(f"Mensagens no buffer: {len(obter_historico(memoria_token))}") # !! Monitoramento
        # print(memoria) # !! Monitoramento
        
        print("\n--- Métricas ---")
        print(f"Latência router: {latencia_router:.3f} s")
        print(f"Latência resposta: {latencia_resposta:.3f} s")
        print(f"Latência total: {latencia_total:.3f} s")
        print(f"Tokens entrada: {tokens_entrada}")
        print(f"Tokens saída: {tokens_saida}. Total: {tokens_entrada + tokens_saida}")

    elif classificacao == "estruturada": # executa chain estruturada (Pydantic)

        history = obter_historico(memoria_token)
        
        inicio_resposta = time.perf_counter()
        
        dados_chain_estruturada = executar_chain_estruturada(history, pergunta)
        
        resposta, tokens_entrada, tokens_saida = dados_chain_estruturada
        
        latencia_resposta = time.perf_counter() - inicio_resposta
        latencia_total = latencia_router + latencia_resposta
        
        # Exibe resposta
        print("\nChargeGrid Assistant:")
        print(resposta) # !! Monitoramento

        # Salva pergunta + resposta na memória
        salvar_turno(memoria_token, pergunta, resposta)
        print(f"Mensagens no buffer: {len(obter_historico(memoria_token))}")

        # print(memoria)
        
        print("\n--- Métricas ---")
        print(f"Latência router: {latencia_router:.3f} s")
        print(f"Latência resposta: {latencia_resposta:.3f} s")
        print(f"Latência total: {latencia_total:.3f} s")
        print(f"Tokens entrada: {tokens_entrada}")
        print(f"Tokens saída: {tokens_saida}. Total = {tokens_entrada + tokens_saida}")
    
    else: print("Tivemos um problema em processar sua mensagem! Por favor, reenvie-a.") # !! Monitoramento