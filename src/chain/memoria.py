from langchain_classic.memory import ConversationTokenBufferMemory

def criar_memoria(llm):
    '''Cria memória conversacional baseada em TokenBuffer'''
    
    return (
        
        ConversationTokenBufferMemory (
            llm = llm,
            max_token_limit = 2300,
            memory_key = "history",
            return_messages = True,
        )

    )
    
def obter_historico(memoria):
    '''Recupera o histórico atual da conversa'''
    
    dados_memoria = memoria.load_memory_variables({})
    
    return dados_memoria["history"]

def salvar_turno(memoria, pergunta, resposta):
    '''Salva o turno de conversa atual na memória '''
    
    memoria.save_context(
        {"pergunta": pergunta},
        {"resposta": resposta}
    )
    