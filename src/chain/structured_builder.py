from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from langchain_core.exceptions import OutputParserException

from schemas.consulta_recarga import ConsultaSessoesSemana 
from recursos import _carregar_dados_mock, _carregar_system_prompt, _formatar_contexto_operacional, contar_tokens_entrada

from dotenv import load_dotenv
import os

import tiktoken

# Objeto encoder/tokenizer
enc = tiktoken.get_encoding("cl100k_base")

load_dotenv()

model = os.getenv("OLLAMA_MODEL")
api_key = os.getenv("OLLAMA_API_KEY")

parser_pydantic = PydanticOutputParser(pydantic_object=ConsultaSessoesSemana) 

prompt = ChatPromptTemplate.from_messages([

("system", _carregar_system_prompt() + "\n{format_instructions}"
+ "\n\n"
+ "Contexto_operacional>\n"
+ "{contexto}\n"
),

("placeholder", "{history}"),

("human", "Pergunta do operador: {pergunta}"),
]).partial(format_instructions=parser_pydantic.get_format_instructions())

llm = ChatOllama(
model=model,
num_precit = 1024,
base_url="https://ollama.com",
client_kwargs={
    "headers": {
        "Authorization": f"Bearer {api_key}"
    }
}
)

chain_pydantic = prompt | llm 

def executar_chain_estruturada(history, pergunta)->str:
    '''
    Quando chamada, executa uma chain diferente da chain conversacional, retornando uma string padronizada contendo 
    os dados dos campos do schema Pydantic ConsultaSessoesSemana. Trata exceção de OutputParser (campos obrigatórios
    no schema não preenchidos, por exemplo)
    '''
    
    try: 
        
        dados_mock = _carregar_dados_mock()
        
        tokens_entrada = contar_tokens_entrada(history, pergunta, dados_mock)
        
        resposta = chain_pydantic.invoke({
            "contexto": _formatar_contexto_operacional(dados_mock),
            "history": history,
            "pergunta": pergunta,
        })
        
        tokens_saida = len(enc.encode(resposta.content))
        
        resposta = parser_pydantic.invoke(resposta)
        
        resposta_formatada = f'''
            Nesta semana foram registradas {resposta.num_sessoes} sessões de recarga,
            com duração média de {resposta.duracao_media} por sessão.

            Total de energia fornecida na semana: {resposta.energia_fornecida} kWh.
            O carregador mais utilizado foi o carregador {resposta.carregador_mais_usado},
            com {resposta.sessoes_carregador_mais_usado} sessões ({resposta.percentual_sessoes_carregador_mais_usado}% do total).
        '''
        
        return (resposta_formatada, tokens_entrada, tokens_saida)
            
    except OutputParserException: # Como a saída vai ser consumida apenas pelo usuário, apenas retorna uma mensagem de erro sem encerrar sessão
        return ("Não foi possível gerar a resposta estruturada para essa consulta", 0, 0)
