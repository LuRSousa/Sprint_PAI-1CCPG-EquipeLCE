from pydantic import BaseModel, Field, field_validator
from typing import Literal


class ConsultaSessoesSemana(BaseModel):
    
    num_sessoes:                    int     = Field(
        default=0, descrption="Número de sessões registradas na semana corrente"
        )
    duracao_media:                  str     = Field(
        default=0, description="Duração média no formato hh/mm das sessões registradas na semana corrente"
        )
    energia_fornecida:              float   = Field(
        default=0, description="Total de energia fornecida por todos os carregadores na semana corrente na unidade kWh"
        )
    carregador_mais_usado:          int     = Field(
        defaul=None, description="ID do carregador que apresenta o maior número de sessões na semana corrente"
        )
    sessoes_carregador_mais_usado:  int     = Field(
        default=0, description="Número de sessões do carregador que teve maior número de sessões na semana corrente"
        )
    
    @field_validator("carregador_mais_usado")
    @classmethod
    def validar_carregador(cls, carregador):
        if carregador < 1 or carregador > 5:
            raise ValueError("Status de sessão inválido")
        return carregador


class RotaConsulta(BaseModel):
    classificacao: Literal["estruturada", "nao_estruturada"]