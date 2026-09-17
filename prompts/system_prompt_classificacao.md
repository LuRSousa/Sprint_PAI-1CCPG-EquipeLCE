prompt = ChatPromptTemplate.from_messages([
    
    ("system", "Classifique se o usuário está pedindo por um relatório das sessões da semana corrente: \n{format_instructions}"
    ),
        
    ("human", "Pergunta do operador: {pergunta}")

    ]).partial(format_instructions=parser.get_format_instructions())

sempre retorna "estruturada"