from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama

from schemas.consulta_recarga import ConsultaSessoesSemana 
from recursos import _carregar_dados_mock, _carregar_system_prompt

from dotenv import load_dotenv
import os

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
base_url="https://ollama.com",
client_kwargs={
    "headers": {
        "Authorization": f"Bearer {api_key}"
    }
}
)

chain_pydantic = prompt | llm | parser_pydantic

def executar_chain_estruturada(history, pergunta):
 
    resposta = chain_pydantic.invoke({
        "contexto": _carregar_dados_mock(),
        "history": history,
        "pergunta": pergunta,
    })
    
    resposta_formatada = f'''
        Nesta semana foram registradas {resposta.num_sessoes} sessões de recarga,
        com duração média de {resposta.duracao_media} por sessão.

        Total de energia fornecida na semana: {resposta.energia_fornecida} kWh.
        O carregador mais utilizado foi o carregador {resposta.carregador_mais_usado},
        com {resposta.sessoes_carregador_mais_usado} sessões ({resposta.percentual_sessoes_carregador_mais_usado}% do total).
    '''
    
    return resposta_formatada