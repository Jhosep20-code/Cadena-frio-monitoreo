"""
Monitor de cadena de frio farmaceutica.
Valida lecturas de temperatura segun el rango exigido para
almacenamiento de medicamentos termolabiles (2 C a 8 C).
"""

TEMP_MIN = 2.0
TEMP_MAX = 8.0


class LecturaInvalida(Exception):
    """Se lanza cuando la lectura no es un valor numerico utilizable."""


def validar_lectura(temperatura):
    """Convierte y valida que la lectura sea un numero real."""
    if isinstance(temperatura, bool) or temperatura is None:
        raise LecturaInvalida("La lectura no es un valor numerico")
    try:
        return float(temperatura)
    except (TypeError, ValueError):
        raise LecturaInvalida("La lectura no es un valor numerico")


def clasificar(temperatura):
    """Devuelve el estado de una lectura: OK, ALERTA_BAJA o ALERTA_ALTA."""
    valor = validar_lectura(temperatura)
    if valor < TEMP_MIN:
        return "ALERTA_BAJA"
    if valor > TEMP_MAX:
        return "ALERTA_ALTA"
    return "OK"


def hay_excursion(lecturas):
    """Indica si al menos una lectura salio del rango permitido."""
    return any(clasificar(t) != "OK" for t in lecturas)


def promedio(lecturas):
    """Promedio de un conjunto de lecturas validas."""
    if not lecturas:
        raise LecturaInvalida("No hay lecturas para promediar")
    valores = [validar_lectura(t) for t in lecturas]
    return sum(valores) / len(valores)


def resumen(lecturas):
    """Genera el resumen diario que consume el acta de cumplimiento."""
    valores = [validar_lectura(t) for t in lecturas]
    if not valores:
        raise LecturaInvalida("No hay lecturas para resumir")
    return {
        "total": len(valores),
        "minima": min(valores),
        "maxima": max(valores),
        "promedio": round(sum(valores) / len(valores), 2),
        "excursiones": sum(1 for v in valores if clasificar(v) != "OK"),
        "estado": "NO CONFORME" if hay_excursion(valores) else "CONFORME",
    }


if __name__ == "__main__":
    demo = [4.1, 4.5, 5.0, 3.8, 4.2]
    print("Resumen de la jornada:", resumen(demo))
