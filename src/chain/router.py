from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from schemas.consulta_recarga import RotaConsulta

def classificar_prompt(llm, pergunta): 
    
    parser = PydanticOutputParser(pydantic_object=RotaConsulta)

    prompt = ChatPromptTemplate.from_messages([
        
        ("system", "Classifique se o usuário está pedindo por um relatório das sessões da semana corrente.\n{format_instructions}"
        ),
            
        ("human", "Pergunta do operador: {pergunta}")
        
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser

    resposta = chain.invoke({
        "pergunta": pergunta,
    })
    
    return resposta.classificacao