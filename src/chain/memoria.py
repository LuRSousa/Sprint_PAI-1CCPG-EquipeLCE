from langchain_classic.memory import ConversationTokenBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory

import tiktoken

_enc = tiktoken.get_encoding("cl100k_base")


def _tokens(mensagem):
    conteudo = mensagem.content if isinstance(mensagem.content, str) else str(mensagem.content)
    return len(_enc.encode(conteudo))


class HistoricoTokenBuffer(BaseChatMessageHistory):
    """
    Adaptador entre RunnableWithMessageHistory e
    ConversationTokenBufferMemory.

    Mantém o histórico de mensagens utilizado pelo
    RunnableWithMessageHistory e aplica o limite de tokens
    definido pela ConversationTokenBufferMemory.
    """

    def __init__(self, memoria):
        self.memoria = memoria

    @property
    def messages(self):
        return self.memoria.chat_memory.messages

    def add_messages(self, messages):
        self.memoria.chat_memory.add_messages(messages)
        # Aplica o limite de tokens da memória. O RunnableWithMessageHistory grava as mensagens direto
        # no histórico, sem passar pelo save_context (onde o ConversationTokenBufferMemory cortaria as
        # mais antigas); sem isto, o histórico crescia sem limite. Corta de dois em dois (pergunta e
        # resposta) e mantém sempre o último turno.
        historico = self.memoria.chat_memory.messages
        while len(historico) > 2 and sum(_tokens(m) for m in historico) > self.memoria.max_token_limit:
            del historico[:2]

    def clear(self):
        self.memoria.clear()


def criar_memoria(llm):
    """Cria memória conversacional baseada em TokenBuffer."""

    return ConversationTokenBufferMemory(
        llm=llm,
        max_token_limit=2300,
        memory_key="history",
        return_messages=True,
    )


def obter_historico(memoria):
    """Recupera o histórico atual da conversa."""

    dados_memoria = memoria.load_memory_variables({})
    return dados_memoria["history"]


def salvar_turno(memoria, pergunta, resposta):
    """
    Salva manualmente um turno na memória.

    Mantida para compatibilidade com outros testes ou partes
    do projeto que ainda utilizem essa função.
    """

    memoria.save_context(
        {"pergunta": pergunta},
        {"resposta": resposta}
    )