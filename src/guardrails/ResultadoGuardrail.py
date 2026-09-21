from pydantic import BaseModel, Field


class ResultadoGuardrail(BaseModel):
    bloqueada: bool = Field(
        default=False,
        description="Indica se a pergunta ou resposta foi bloqueada por um guardrail"
    )

    categoria: str | None = Field(
        default=None,
        description="Categoria do bloqueio, quando houver"
    )

    motivo: str | None = Field(
        default=None,
        description="Motivo pelo qual o conteúdo foi bloqueado"
    )

    mensagem_usuario: str | None = Field(
        default=None,
        description="Mensagem segura que deve ser apresentada ao usuário"
    )