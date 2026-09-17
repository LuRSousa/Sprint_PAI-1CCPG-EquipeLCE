from pydantic import BaseModel, Field, field_validator
from typing import Literal


class ConsultaSessoesSemana(BaseModel):
    
    num_sessoes:                    int     = Field(
        default=0, description="Número de sessões registradas na semana corrente"
        )
    duracao_media:                  str     = Field(
        default="00/00", description="Duração média no formato hh/mm das sessões registradas na semana corrente"
        )
    energia_fornecida:              float   = Field(
        default=0, description="Total de energia fornecida por todos os carregadores na semana corrente na unidade kWh"
        )
    carregador_mais_usado:          int | None    = Field(
        default=None, description="ID do carregador que apresenta o maior número de sessões na semana corrente"
        )
    sessoes_carregador_mais_usado:  int     = Field(
        default=0, description="Número de sessões do carregador que teve maior número de sessões na semana corrente"
        )
    percentual_sessoes_carregador_mais_usado:  float     = Field(
        default=0, description="Percentual do número de sessões realizadas pelo carregador com mais sessões na semana em relação ao número total de sessões da semana corrente"
        )
    
    @field_validator("carregador_mais_usado")
    @classmethod
    def validar_carregador(cls, carregador):
        if carregador is not None and (carregador < 1 or carregador > 5):
            raise ValueError("ID de carregador inválido")
        return carregador
    
    @field_validator("percentual_sessoes_carregador_mais_usado")
    @classmethod
    def validar_percentual(cls, percentual):
        if not 0 <= percentual <= 100:
            raise ValueError(
                "O percentual deve estar entre 0 e 100"
            )

        return percentual

class RotaConsulta(BaseModel):
    classificacao: Literal["estruturada", "nao_estruturada"]