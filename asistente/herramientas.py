"""
Capa de herramientas: traduce lo que pide el modelo a funciones deterministas.

Cada funcion valida sus argumentos, ejecuta `monitor.py` de la TA1 sobre las
lecturas del repositorio y devuelve un diccionario autodescriptivo. Ningun
error sale como excepcion hacia el modelo: se devuelve como {"error": ...}
para que el asistente pueda explicarlo al usuario.
"""

import json
import os
from datetime import date, datetime, timedelta

from src.monitor import clasificar, resumen

from asistente.alertas import DESTINATARIOS, enviar
from asistente.repositorio import (
    INTERVALO_MIN, SEDES, hoy, ahora, lecturas_del_dia, lecturas_esperadas, ultima_lectura,
)

MAX_DIAS_PERIODO = 31
MAX_HORAS_VENTANA = 24
UMBRAL_SENSOR_MIN = 30          # sobre esta antiguedad se considera fuera de linea
RUTA_BITACORA = os.path.join("bitacora", "auditoria.jsonl")


class AccesoDenegado(Exception):
    pass


def _error(codigo, mensaje):
    return {"error": codigo, "mensaje": mensaje}


def _fecha(texto, campo):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        raise ValueError("%s debe tener el formato AAAA-MM-DD" % campo)


def _momento(texto, campo):
    try:
        return datetime.strptime(texto, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        raise ValueError("%s debe tener el formato AAAA-MM-DDTHH:MM" % campo)


def _verificar_sede(sede, autorizadas):
    if sede not in SEDES:
        raise ValueError("La sede %s no existe" % sede)
    if sede not in autorizadas:
        raise AccesoDenegado(sede)


# --------------------------------------------------------------- herramientas

def listar_sedes_autorizadas(autorizadas):
    return {"sedes": [{"id": s, "nombre": SEDES[s]} for s in autorizadas if s in SEDES]}


def consultar_temperatura_actual(sede, autorizadas):
    _verificar_sede(sede, autorizadas)
    registro = ultima_lectura(sede)
    if registro is None:
        return _error("SIN_DATOS", "No hay lecturas recientes para %s" % sede)

    marca, temperatura = registro
    antiguedad = int((ahora() - marca).total_seconds() // 60)
    return {
        "sede": sede,
        "lectura": temperatura,
        "unidad": "C",
        "estado": clasificar(temperatura),
        "registrada": marca.strftime("%Y-%m-%dT%H:%M"),
        "antiguedad_min": antiguedad,
        "sensor_en_linea": antiguedad <= UMBRAL_SENSOR_MIN,
    }


def consultar_lecturas_periodo(sede, desde, hasta, solo_alertas, autorizadas):
    _verificar_sede(sede, autorizadas)
    inicio, fin = _momento(desde, "desde"), _momento(hasta, "hasta")
    if fin <= inicio:
        return _error("FECHA_INVALIDA", "'hasta' debe ser posterior a 'desde'")
    if (fin - inicio) > timedelta(hours=MAX_HORAS_VENTANA):
        return _error("PERIODO_EXCEDIDO", "La ventana no puede superar %d horas" % MAX_HORAS_VENTANA)
    if inicio.date() > hoy():
        return _error("FECHA_INVALIDA", "La fecha solicitada aun no ha ocurrido")

    filas = []
    dia = inicio.date()
    while dia <= fin.date():
        for marca, temperatura in lecturas_del_dia(sede, dia):
            if inicio <= marca <= fin:
                estado = clasificar(temperatura)
                if solo_alertas and estado == "OK":
                    continue
                filas.append({"hora": marca.strftime("%H:%M"), "t": temperatura, "estado": estado})
        dia += timedelta(days=1)

    if not filas:
        return _error("SIN_DATOS", "No hay lecturas en esa ventana")
    return {"sede": sede, "desde": desde, "hasta": hasta, "unidad": "C",
            "total": len(filas), "lecturas": filas}


def consultar_excursiones_termicas(sede, fecha_inicio, fecha_fin, tipo, autorizadas):
    _verificar_sede(sede, autorizadas)
    inicio, fin = _fecha(fecha_inicio, "fecha_inicio"), _fecha(fecha_fin, "fecha_fin")
    if fin < inicio:
        return _error("FECHA_INVALIDA", "fecha_fin es anterior a fecha_inicio")
    if inicio > hoy():
        return _error("FECHA_INVALIDA", "La fecha solicitada aun no ha ocurrido")
    if (fin - inicio).days + 1 > MAX_DIAS_PERIODO:
        return _error("PERIODO_EXCEDIDO", "El periodo no puede superar %d dias" % MAX_DIAS_PERIODO)

    episodios, abierto = [], None
    dia = inicio
    while dia <= min(fin, hoy()):
        for marca, temperatura in lecturas_del_dia(sede, dia):
            estado = clasificar(temperatura)
            fuera = estado != "OK" and tipo in ("TODAS", estado)
            if fuera:
                if abierto is None:
                    abierto = {"tipo": estado, "inicio": marca, "fin": marca,
                               "valor_extremo": temperatura, "lecturas_fuera_de_rango": 1}
                else:
                    abierto["fin"] = marca
                    abierto["lecturas_fuera_de_rango"] += 1
                    peor = max if estado == "ALERTA_ALTA" else min
                    abierto["valor_extremo"] = peor(abierto["valor_extremo"], temperatura)
            elif abierto is not None:
                episodios.append(abierto)
                abierto = None
        dia += timedelta(days=1)
    if abierto is not None:
        episodios.append(abierto)

    formateados = [{
        "tipo": e["tipo"],
        "inicio": e["inicio"].strftime("%Y-%m-%dT%H:%M"),
        "fin": e["fin"].strftime("%Y-%m-%dT%H:%M"),
        "duracion_estimada_min": int((e["fin"] - e["inicio"]).total_seconds() // 60) + INTERVALO_MIN,
        "valor_extremo": e["valor_extremo"],
        "lecturas_fuera_de_rango": e["lecturas_fuera_de_rango"],
    } for e in episodios]

    return {"sede": sede, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
            "unidad": "C", "total_episodios": len(formateados), "episodios": formateados}


def generar_resumen_jornada(sede, fecha, autorizadas):
    _verificar_sede(sede, autorizadas)
    dia = _fecha(fecha, "fecha")
    if dia > hoy():
        return _error("FECHA_INVALIDA", "La fecha solicitada aun no ha ocurrido")

    registros = lecturas_del_dia(sede, dia)
    if not registros:
        return _error("SIN_DATOS", "No hay lecturas registradas el %s" % fecha)

    base = resumen([t for _, t in registros])          # funcion original de la TA1
    esperadas = lecturas_esperadas(dia)

    return {
        "sede": sede,
        "fecha": fecha,
        "parcial": dia == hoy(),
        "unidad": "C",
        "total_lecturas": base["total"],
        "lecturas_esperadas": esperadas,
        "cobertura_pct": round(base["total"] / esperadas * 100, 1),
        "minima": base["minima"],
        "maxima": base["maxima"],
        "promedio": base["promedio"],
        # Se renombra: resumen() cuenta LECTURAS fuera de rango, no episodios.
        "lecturas_fuera_de_rango": base["excursiones"],
        "estado": base["estado"],
    }


def notificar_responsable(sede, fecha, destinatario, motivo, autorizadas):
    """Avisa al responsable, pero solo si la excursion existe en el registro."""
    _verificar_sede(sede, autorizadas)
    if destinatario not in DESTINATARIOS:
        return _error("FECHA_INVALIDA", "Destinatario desconocido: %s" % destinatario)

    verificacion = consultar_excursiones_termicas(sede, fecha, fecha, "TODAS", autorizadas)
    if "error" in verificacion:
        return verificacion
    if verificacion["total_episodios"] == 0:
        return _error("SIN_EXCURSION",
                      "No hay excursiones registradas en %s el %s: no se envia la alerta"
                      % (sede, fecha))

    episodio = verificacion["episodios"][0]
    asunto = "Excursion termica en %s el %s" % (SEDES[sede], fecha)
    alerta = enviar(destinatario, asunto, motivo,
                    {"sede": sede, "fecha": fecha, "episodios": verificacion["episodios"]})

    return {"alerta_id": alerta["id"], "estado": alerta["estado"], "canal": alerta["canal"],
            "destinatario": alerta["nombre_destinatario"], "momento": alerta["momento"],
            "asunto": asunto, "episodios_adjuntos": verificacion["total_episodios"],
            "valor_extremo": episodio["valor_extremo"], "unidad": "C"}


EJECUTORES = {
    "listar_sedes_autorizadas": listar_sedes_autorizadas,
    "consultar_temperatura_actual": consultar_temperatura_actual,
    "consultar_lecturas_periodo": consultar_lecturas_periodo,
    "consultar_excursiones_termicas": consultar_excursiones_termicas,
    "generar_resumen_jornada": generar_resumen_jornada,
    "notificar_responsable": notificar_responsable,
}


def ejecutar(nombre, argumentos, autorizadas):
    """Punto unico de entrada. Nunca lanza: devuelve el error como dato."""
    if nombre not in EJECUTORES:
        return _error("FALLO_INTERNO", "Funcion desconocida: %s" % nombre)
    try:
        return EJECUTORES[nombre](autorizadas=autorizadas, **argumentos)
    except AccesoDenegado:
        return _error("ACCESO_DENEGADO", "El usuario no tiene acceso a esa sede")
    except (ValueError, TypeError) as e:
        return _error("FECHA_INVALIDA", str(e))
    except Exception as e:                                # red de seguridad
        return _error("FALLO_INTERNO", type(e).__name__)


def auditar(entrada):
    """Registra la llamada en un archivo JSON Lines para la trazabilidad (R4)."""
    try:
        os.makedirs(os.path.dirname(RUTA_BITACORA), exist_ok=True)
        with open(RUTA_BITACORA, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass        # la bitacora nunca debe tumbar la respuesta al usuario


# ----------------------------------------------------- esquemas para el modelo

def cargar_esquemas():
    ruta = os.path.join(os.path.dirname(__file__), "herramientas.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)
