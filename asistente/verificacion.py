"""
Mitigacion M1 de la TA2: verificacion de procedencia numerica.

Toda cifra u hora que aparezca en la respuesta debe existir en los resultados
de las funciones ejecutadas en ese turno. Si alguna no tiene respaldo, se
marca como huerfana y la interfaz lo advierte junto a la respuesta.

Es un control barato y determinista: no depende de que el modelo obedezca.
"""

import json
import re

PATRON = re.compile(r"\d{1,2}:\d{2}|\d+(?:[.,]\d+)?")

# Constantes que el propio prompt autoriza a nombrar sin consultar nada.
CONSTANTES = {"2.0", "8.0", "2", "8", "95", "100", "150", "15", "24", "31", "1"}


def _numeros(texto):
    return set(PATRON.findall(texto.replace(",", ".")))


def verificar_procedencia(respuesta, resultados):
    """Devuelve (respuesta, huerfanas). No reescribe el texto: solo audita."""
    if not resultados:
        return respuesta, set()

    respaldadas = _numeros(json.dumps(resultados, ensure_ascii=False, default=str)) | CONSTANTES
    huerfanas = _numeros(respuesta) - respaldadas
    return respuesta, huerfanas
