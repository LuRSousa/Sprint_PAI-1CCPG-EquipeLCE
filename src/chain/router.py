from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

import sys
from pathlib import Path

# Adiciona a pasta raiz 'src' ao sys.path
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from recursos import _carregar_router_system_prompt
from schemas.consulta_recarga import RotaConsulta

import tiktoken

# Objeto encoder/tokenizer
enc = tiktoken.get_encoding("cl100k_base")

def classificar_prompt(llm, pergunta) -> str: 
    '''Ecxecuta uma chain dedicada à classificar o user prompt, determinando se ele está pedindo por informações 
    das sessões de recarga da semana correte ou não. Devolve uma string (validada por um schema Pydantic)
    para o builder.py.
    '''
    
    parser = PydanticOutputParser(pydantic_object=RotaConsulta)

    prompt = ChatPromptTemplate.from_messages([
        
        ("system", _carregar_router_system_prompt() + ".\n{format_instructions}"
        ),
            
        ("human", "Pergunta do operador: {pergunta}")
        
    ]).partial(format_instructions=parser.get_format_instructions())

    chain_llm = prompt | llm

    # Executa a LLM
    resposta_llm = chain_llm.invoke({
        "pergunta": pergunta,
    })

    # Mede a saída produzida pela LLM
    tokens_saida = len(enc.encode(resposta_llm.content))

    # Converte a resposta para RotaConsulta
    resposta = parser.invoke(resposta_llm)

    # Mede a entrada
    prompt_formatado = prompt.invoke({
        "pergunta": pergunta,
    })

    tokens_entrada = len(enc.encode(pergunta))

    tokens_total = tokens_entrada + tokens_saida

    return (resposta.classificacao, tokens_total)