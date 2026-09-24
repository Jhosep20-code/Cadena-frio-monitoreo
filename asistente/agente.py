"""
Agente: implementa el ciclo "el modelo pide una funcion, el equipo la ejecuta
y le devuelve el resultado", que es el mismo de `requires_action` descrito en
la TA2. Aqui el historial lo guarda la aplicacion en lugar del servidor.

Devuelve un diccionario con el texto de la respuesta, la traza de llamadas
(argumentos, resultado y duracion de cada una) y las cifras sin respaldo que
detecta la verificacion de procedencia. La traza es lo que la interfaz
muestra en el panel del ciclo.
"""

import copy
import hashlib
import json
import os
import time
from datetime import datetime

from openai import OpenAI

from asistente.herramientas import auditar, cargar_esquemas, ejecutar
from asistente.verificacion import verificar_procedencia

PROVEEDORES = {
    "gemini": {
        "etiqueta": "Google Gemini (capa gratuita)", "variable": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "modelo": "gemini-3.6-flash", "consola": "https://aistudio.google.com/apikey",
        # El modo strict de los esquemas es especifico de OpenAI: se retira.
        "admite_strict": False,
    },
    "groq": {
        "etiqueta": "Groq (capa gratuita)", "variable": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "modelo": "llama-3.3-70b-versatile", "consola": "https://console.groq.com/keys",
        "admite_strict": False,
    },
    "openai": {
        "etiqueta": "OpenAI (requiere saldo)", "variable": "OPENAI_API_KEY",
        "base_url": None, "modelo": "gpt-4o-mini",
        "consola": "https://platform.openai.com/api-keys", "admite_strict": True,
    },
}

# Mitigacion de costos (guia interna, seccion 7): en desarrollo se cachean las
# respuestas del modelo, de modo que repetir la demostracion no consume cuota.
CACHE_ACTIVA = os.environ.get("CACHE_RESPUESTAS", "1") == "1"
RUTA_CACHE = os.path.join("bitacora", "cache_respuestas.json")

MAX_RONDAS = 5          # rondas de llamadas a funciones por pregunta
MAX_LLAMADAS = 8        # funciones por pregunta, sumando todas las rondas
DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def _clave_cache(proveedor, historial, autorizadas):
    crudo = json.dumps([proveedor, historial, sorted(autorizadas)], ensure_ascii=False)
    return hashlib.sha256(crudo.encode()).hexdigest()[:16]


def _leer_cache(clave):
    if not CACHE_ACTIVA or not os.path.exists(RUTA_CACHE):
        return None
    try:
        with open(RUTA_CACHE, encoding="utf-8") as f:
            guardado = json.load(f).get(clave)
    except (OSError, json.JSONDecodeError):
        return None
    if guardado is None:
        return None
    guardado["huerfanas"] = set(guardado.get("huerfanas", []))
    guardado["desde_cache"] = True
    return guardado


def _escribir_cache(clave, salida):
    if not CACHE_ACTIVA:
        return
    try:
        os.makedirs(os.path.dirname(RUTA_CACHE), exist_ok=True)
        datos = {}
        if os.path.exists(RUTA_CACHE):
            with open(RUTA_CACHE, encoding="utf-8") as f:
                datos = json.load(f)
        datos[clave] = {"texto": salida["texto"], "traza": salida["traza"],
                        "huerfanas": sorted(salida["huerfanas"])}
        with open(RUTA_CACHE, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
    except (OSError, json.JSONDecodeError, TypeError):
        pass


def esquemas_para(proveedor):
    """Groq no admite el modo strict; se retira sin tocar el resto del esquema."""
    esquemas = copy.deepcopy(cargar_esquemas())
    if not PROVEEDORES[proveedor]["admite_strict"]:
        for e in esquemas:
            e["function"].pop("strict", None)
    return esquemas


def crear_cliente(proveedor, clave):
    datos = PROVEEDORES[proveedor]
    return OpenAI(api_key=clave, base_url=datos["base_url"])


def modelos_disponibles(cliente):
    """Lista los modelos que acepta el proveedor.

    Los nombres cambian con frecuencia (Google y Groq retiran versiones cada
    pocas semanas), asi que la interfaz ofrece consultarlos en vivo en lugar
    de confiar en un nombre fijo escrito en el codigo.
    """
    try:
        return sorted(m.id for m in cliente.models.list().data)
    except Exception as e:
        return ["No se pudo consultar: %s" % type(e).__name__]


def instrucciones_del_turno():
    ahora = datetime.now()
    return "Fecha y hora actual en Lima: %s (%s)." % (
        ahora.strftime("%Y-%m-%d %H:%M"), DIAS[ahora.weekday()])


def responder(cliente, proveedor, prompt_sistema, historial, autorizadas,
              temperatura=0.2, modelo=None):
    """Ejecuta un turno completo. historial: [{"role","content"}, ...]."""
    modelo = modelo or PROVEEDORES[proveedor]["modelo"]
    clave = _clave_cache(proveedor + "|" + modelo, historial, autorizadas)
    guardado = _leer_cache(clave)
    if guardado is not None:
        return guardado

    mensajes = [{"role": "system", "content": prompt_sistema + "\n\n" + instrucciones_del_turno()}]
    mensajes += [{"role": m["role"], "content": m["content"]} for m in historial]

    esquemas = esquemas_para(proveedor)
    traza, rondas, llamadas = [], 0, 0

    respuesta = cliente.chat.completions.create(
        model=modelo, messages=mensajes,
        tools=esquemas, tool_choice="auto", temperature=temperatura)
    mensaje = respuesta.choices[0].message

    # Equivalente a: while run.status == "requires_action"
    while getattr(mensaje, "tool_calls", None):
        rondas += 1
        llamadas += len(mensaje.tool_calls)
        if rondas > MAX_RONDAS or llamadas > MAX_LLAMADAS:
            return {"texto": "No pude completar la consulta: la pregunta exige "
                    "demasiadas consultas. Intente acotarla a una sede y un periodo.",
                    "traza": traza, "huerfanas": set()}

        mensajes.append({"role": "assistant", "content": mensaje.content or "",
                         "tool_calls": [t.model_dump() for t in mensaje.tool_calls]})

        for llamada in mensaje.tool_calls:
            nombre = llamada.function.name
            try:
                argumentos = json.loads(llamada.function.arguments or "{}")
            except json.JSONDecodeError:
                argumentos = {}

            inicio = time.time()
            resultado = ejecutar(nombre, argumentos, autorizadas)   # aqui se valida el acceso
            ms = int((time.time() - inicio) * 1000)

            traza.append({"ronda": rondas, "funcion": nombre, "argumentos": argumentos,
                          "resultado": resultado, "ms": ms})
            auditar({"momento": datetime.now().isoformat(timespec="seconds"),
                     "funcion": nombre, "argumentos": argumentos,
                     "error": resultado.get("error"), "ms": ms})

            mensajes.append({"role": "tool", "tool_call_id": llamada.id, "name": nombre,
                             "content": json.dumps(resultado, ensure_ascii=False)})

        respuesta = cliente.chat.completions.create(
            model=modelo, messages=mensajes,
            tools=esquemas, tool_choice="auto", temperature=temperatura)
        mensaje = respuesta.choices[0].message

    texto = mensaje.content or "No obtuve respuesta del modelo."
    texto, huerfanas = verificar_procedencia(texto, [t["resultado"] for t in traza])
    salida = {"texto": texto, "traza": traza, "huerfanas": huerfanas, "desde_cache": False}

    # Una respuesta que envio una alerta no se cachea: el envio debe repetirse.
    if not any(p["funcion"] == "notificar_responsable" for p in traza):
        _escribir_cache(clave, salida)
    return salida
