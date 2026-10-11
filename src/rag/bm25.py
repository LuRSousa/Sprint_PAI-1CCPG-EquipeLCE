"""Busca por palavra-chave (BM25), usada junto com a busca semântica na busca híbrida.

O embedding acha trechos com sentido parecido, mas às vezes perde a palavra exata da pergunta:
no eval, "choque elétrico" trouxe a seção de alagamento e não a 4.3 (Choque elétrico). O BM25
pontua cada trecho pelas palavras que ele tem em comum com a pergunta e dá mais peso às palavras
raras na base, então "choque" pesa mais que "carregador", que aparece em quase todo trecho.

Pontuação de um trecho (BM25 Okapi), somando cada palavra p da pergunta:
    idf(p) * f * (k1 + 1) / (f + k1 * (1 - b + b * tamanho_do_trecho / tamanho_medio))
f = quantas vezes p aparece no trecho; idf(p) = log(1 + (N - n + 0,5) / (n + 0,5)),
com N trechos na base e n trechos que têm a palavra. k1 = 1,5 e b = 0,75 são os valores usuais.

As palavras passam por um "radical" simples (reserva, reservas, reservar -> reserv), para a
pergunta achar o trecho mesmo com outra flexão da palavra. Feito à mão, sem biblioteca nova.
"""
import math
import re
import unicodedata
from collections import Counter

# Palavras que aparecem em qualquer frase e não ajudam a achar o trecho certo
PALAVRAS_VAZIAS = set("""
a ao aos as ate com como da das de dela dele deles do dos e ela ele eles em entre era essa esse
esta este eu foi ha isso isto ja la lhe mais mas me mesmo meu minha muito na nas nem no nos o os
ou para pela pelas pelo pelos por pode posso qual quais quando que quem se sem ser seu sua sao
tem ter um uma umas uns voce vou esta estao sobre tambem so devo deve fazer faz
""".split())

# Terminações tiradas para chegar ao radical (da mais longa para a mais curta; só uma por palavra)
TERMINACOES = sorted("""
amentos imentos amento imento acoes icoes acao icao adoras adores adora ador ancas anca encia
ancia mente idade avel ivel ando endo indo ados idos adas idas ado ido ada ida ar er ir as es
os is a e o s
""".split(), key=len, reverse=True)


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def radical(palavra: str) -> str:
    for fim in TERMINACOES:
        if palavra.endswith(fim) and len(palavra) - len(fim) >= 3:
            return palavra[: -len(fim)]
    return palavra


def palavras(texto: str) -> list[str]:
    """Texto -> radicais das palavras que importam (sem acento, sem palavras vazias)."""
    return [radical(p) for p in re.findall(r"[a-z0-9]+", _sem_acento(texto)) if p not in PALAVRAS_VAZIAS]


class IndiceBM25:
    def __init__(self, textos: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.contagens = [Counter(palavras(t)) for t in textos]
        self.tamanhos = [sum(c.values()) for c in self.contagens]
        self.tamanho_medio = sum(self.tamanhos) / max(len(self.tamanhos), 1)
        n_trechos = len(textos)
        com_palavra = Counter(p for c in self.contagens for p in c)
        self.idf = {p: math.log(1 + (n_trechos - n + 0.5) / (n + 0.5)) for p, n in com_palavra.items()}

    def pontuar(self, consulta: str) -> list[float]:
        termos = set(palavras(consulta))
        pontos = []
        for contagem, tamanho in zip(self.contagens, self.tamanhos):
            total = 0.0
            for p in termos:
                f = contagem.get(p, 0)
                if f:
                    ajuste = self.k1 * (1 - self.b + self.b * tamanho / self.tamanho_medio)
                    total += self.idf[p] * f * (self.k1 + 1) / (f + ajuste)
            pontos.append(total)
        return pontos

    def termos_em_comum(self, consulta: str, indice_trecho: int) -> int:
        return len(set(palavras(consulta)) & set(self.contagens[indice_trecho]))
