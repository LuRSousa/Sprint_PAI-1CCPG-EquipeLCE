from pydantic import BaseModel, Field, field_validator
from typing import Literal


class ConsultaSessoesSemana(BaseModel):
    '''Schema Pydantic com 2 field validators. Utilizado quando router.py classificar o input do usuário como 
    "estruturada", contendo número de sessões, duração média, total de energia fornecdia, carregador mais usado na 
    semana, número de sessões realizados por ele e o quanto elas representam do número total de sessões realizadas na
    semana.
    '''
    
    num_sessoes:                    int     = Field(
        default=0, description="Número de sessões registradas na semana corrente"
        )
    duracao_media:                  str     = Field(
        default="00/00", description="Duração média no formato hh h mm min (ou seja, xxhyymin, se a média for mais que uma hora) ou mm min (ou seja, xxmin, se a média for menor que uma hora) das sessões registradas na semana corrente"
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
    '''Shema Pydantic usado pelo router.py para validar se sua saída uma string, com 2 valores possíveis:
    "estruturada" ou "nao_estruturada"
    '''
    classificacao: Literal["estruturada", "nao_estruturada"]