from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ConsultaRecarga(BaseModel):
    
    id_carregador: Optional[int] = Field(
        default=None,
        description="ID do carregador consultado"
    )

    status: Optional[str] = Field(
        default=None,
        description="Status da sessão de recarga"
    )

    incluir_consumo: bool = Field(
        default=False,
        description="Indica se o consumo de energia deve ser incluído"
    )

    @field_validator("status")
    @classmethod
    def validar_status(cls, valor):
        if valor is not None and valor not in {
            "ativa",
            "concluída",
            "com_falha"
        }:
            raise ValueError("Status de sessão inválido")
        return valor