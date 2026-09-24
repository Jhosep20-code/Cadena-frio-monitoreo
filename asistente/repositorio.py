"""
Repositorio de lecturas de temperatura.

Genera el historico de las camaras de forma DETERMINISTA: la misma sede y la
misma fecha producen siempre las mismas lecturas, de modo que la demostracion
en clase es reproducible y las pruebas pueden verificar valores exactos.

En produccion este modulo se reemplazaria por una consulta a la base de datos
donde los sensores depositan sus lecturas; el resto del asistente no cambia.
"""

import hashlib
import random
from datetime import date, datetime, timedelta

SEDES = {
    "almacen-huancayo": "Almacen Huancayo",
    "almacen-jauja": "Almacen Jauja",
}

INTERVALO_MIN = 15                       # una lectura cada 15 minutos
LECTURAS_POR_DIA = 24 * 60 // INTERVALO_MIN   # 96


def hoy():
    """Fecha actual. Aislada en una funcion para poder fijarla en pruebas."""
    return date.today()


def ahora():
    return datetime.now()


def _semilla(sede, fecha):
    crudo = "%s|%s" % (sede, fecha.isoformat())
    return int(hashlib.md5(crudo.encode()).hexdigest()[:8], 16)


def _eventos(sede, fecha):
    """Incidentes sembrados para que la demostracion tenga algo que contar.

    - Jauja, ayer: excursion alta de 03:15 a 04:00 con pico de 9.6 C y dos
      lecturas perdidas al mediodia (cobertura 97.9 %).
    - Huancayo, hace cuatro dias: excursion baja de 23:00 a 23:30 (1.4 C),
      util para preguntas semanales.
    """
    eventos = {"excursiones": {}, "perdidas": []}
    delta = (hoy() - fecha).days

    if sede == "almacen-jauja" and delta == 1:
        eventos["excursiones"] = {"03:15": 8.4, "03:30": 9.1, "03:45": 9.6, "04:00": 8.7}
        eventos["perdidas"] = ["11:30", "11:45"]

    if sede == "almacen-huancayo" and delta == 4:
        eventos["excursiones"] = {"23:00": 1.8, "23:15": 1.4, "23:30": 1.9}

    return eventos


def lecturas_del_dia(sede, fecha):
    """Devuelve [(datetime, temperatura)] de la jornada, ya ordenadas.

    Si la fecha es hoy, solo llegan las lecturas hasta la hora actual: eso es
    lo que hace que el resumen del dia en curso sea parcial.
    """
    if sede not in SEDES:
        raise ValueError("Sede desconocida: %s" % sede)

    azar = random.Random(_semilla(sede, fecha))
    eventos = _eventos(sede, fecha)
    limite = ahora() if fecha == hoy() else None

    salida = []
    for i in range(LECTURAS_POR_DIA):
        minutos = i * INTERVALO_MIN
        marca = datetime(fecha.year, fecha.month, fecha.day) + timedelta(minutes=minutos)
        if limite is not None and marca > limite:
            break

        etiqueta = "%02d:%02d" % (minutos // 60, minutos % 60)
        if etiqueta in eventos["perdidas"]:
            continue

        if etiqueta in eventos["excursiones"]:
            temperatura = eventos["excursiones"][etiqueta]
        else:
            temperatura = round(azar.uniform(3.6, 5.8), 1)

        salida.append((marca, temperatura))

    return salida


def lecturas_esperadas(fecha):
    """Cuantas lecturas deberia haber a esta altura del dia."""
    if fecha != hoy():
        return LECTURAS_POR_DIA
    transcurridos = ahora().hour * 60 + ahora().minute
    return max(1, transcurridos // INTERVALO_MIN + 1)


def ultima_lectura(sede):
    """Lectura mas reciente disponible, buscando hacia atras si hace falta."""
    for retroceso in range(0, 3):
        dia = hoy() - timedelta(days=retroceso)
        registros = lecturas_del_dia(sede, dia)
        if registros:
            return registros[-1]
    return None
