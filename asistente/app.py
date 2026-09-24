"""
Termo - Asistente de consulta del histórico térmico.

Unidad 2 · TA2 · Herramientas de Desarrollo Profesional - TIC · UTP Huancayo

Disposición:
  cabecera         marca, estado del monitor y modelo en uso
  tablero          una tarjeta por sede, calculada con monitor.py (sin API)
  conversación     a la izquierda
  evidencia        a la derecha: el ciclo del turno como línea de tiempo

Ejecutar desde la raíz del proyecto:
    streamlit run asistente/app.py
"""

import base64
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from asistente import ui
from asistente.agente import (
    MAX_LLAMADAS, MAX_RONDAS, PROVEEDORES, crear_cliente, esquemas_para,
    instrucciones_del_turno, modelos_disponibles, responder,
)
from asistente.herramientas import RUTA_BITACORA, ejecutar
from asistente.repositorio import SEDES, hoy, lecturas_del_dia

AQUI = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Termo · Monitor de cadena de frío",
                   page_icon=":material/thermostat:", layout="wide",
                   initial_sidebar_state="auto")
st.markdown(ui.ESTILOS, unsafe_allow_html=True)

PROMPT = open(os.path.join(AQUI, "prompt_sistema.txt"), encoding="utf-8").read()
LOGO = base64.b64encode(open(os.path.join(AQUI, "logo.svg"), "rb").read()).decode()

AVATAR_ASISTENTE = ":material/ac_unit:"
AVATAR_USUARIO = ":material/person:"

SALUDO = ("Soy **Termo**. Consulto el estado de las cámaras, las excursiones térmicas y el "
          "resumen de cualquier jornada, y puedo avisar al responsable de turno. "
          "Todas las cifras que le muestre salen del monitor, no de mi memoria.")

SUGERENCIAS = [
    ("¿Cómo le fue a Jauja ayer? ¿Hubo algún problema?", "Resumen y excursiones"),
    ("¿Cómo está la cámara de Huancayo en este momento?", "Estado en tiempo real"),
    ("Avisa al químico farmacéutico de turno sobre la excursión de Jauja", "Envío de alerta"),
    ("¿Puedo seguir usando las vacunas que estuvieron en esa cámara?", "Límite sanitario"),
]

estado = st.session_state
estado.setdefault("mensajes", [{"role": "assistant", "content": SALUDO, "traza": []}])
estado.setdefault("pendiente", None)
estado.setdefault("turno_visible", None)


# =============================================================== barra lateral
with st.sidebar:
    st.markdown("#### Proveedor de IA")
    nombres = list(PROVEEDORES)
    proveedor = st.selectbox("Proveedor", nombres, label_visibility="collapsed",
                             format_func=lambda p: PROVEEDORES[p]["etiqueta"])
    datos = PROVEEDORES[proveedor]

    clave = st.text_input(datos["variable"], type="password",
                          value=os.environ.get(datos["variable"], ""),
                          help="Consígala en " + datos["consola"])
    modelo = st.text_input(
        "Modelo", datos["modelo"],
        help="Los proveedores retiran versiones con frecuencia. Si aparece un error de modelo "
             "inexistente, consulte la lista y pegue aquí el nombre vigente.")

    if st.button("Consultar modelos disponibles", icon=":material/list:", use_container_width=True):
        if clave:
            with st.spinner("Consultando"):
                estado.modelos = modelos_disponibles(crear_cliente(proveedor, clave))
        else:
            st.warning("Primero ingrese la clave.")
    if estado.get("modelos"):
        with st.expander("Modelos del proveedor"):
            st.code("\n".join(estado.modelos[:60]), language="text")

    st.markdown("#### Sesión del usuario")
    autorizadas = st.multiselect(
        "Sedes autorizadas", list(SEDES), default=list(SEDES), format_func=lambda s: SEDES[s],
        help="En producción lo fija el servidor al iniciar sesión. Aquí se expone para demostrar "
             "el control de acceso: quite una sede y pregunte por ella.")

    st.markdown("#### Canal de alertas")
    if os.environ.get("WEBHOOK_ALERTAS", "").strip():
        st.caption("Webhook configurado: las alertas se envían al servicio externo.")
    else:
        st.caption("Sin webhook: las alertas se registran en `bitacora/alertas.jsonl`.")

    st.markdown("#### Referencia técnica")
    st.caption("Límites por pregunta: %d rondas · %d llamadas" % (MAX_RONDAS, MAX_LLAMADAS))
    with st.expander("Prompt de sistema", icon=":material/description:"):
        st.code(PROMPT, language="text")
    with st.expander("Herramientas declaradas", icon=":material/build:"):
        for e in esquemas_para(proveedor):
            st.markdown("`%s`" % e["function"]["name"])
            st.caption(e["function"]["description"][:170] + "…")
    with st.expander("Instrucciones de este turno", icon=":material/schedule:"):
        st.code(instrucciones_del_turno(), language="text")

    if st.button("Nueva conversación", icon=":material/restart_alt:", use_container_width=True):
        estado.mensajes = [{"role": "assistant", "content": SALUDO, "traza": []}]
        estado.turno_visible = None
        st.rerun()


# ==================================================================== cabecera
st.markdown(ui.cabecera(LOGO, modelo, PROVEEDORES[proveedor]["etiqueta"].split(" (")[0]),
            unsafe_allow_html=True)


# ===================================================================== tablero
@st.cache_data(ttl=60, show_spinner=False)
def datos_tablero(sedes):
    """Una fila por sede. Se calcula con las mismas herramientas, sin llamar al modelo."""
    todas = list(SEDES)
    filas = []
    for sede in sedes:
        actual = ejecutar("consultar_temperatura_actual", {"sede": sede}, todas)
        resumen = ejecutar("generar_resumen_jornada", {"sede": sede, "fecha": hoy().isoformat()}, todas)
        semana = ejecutar("consultar_excursiones_termicas", {
            "sede": sede, "fecha_inicio": (hoy() - timedelta(days=6)).isoformat(),
            "fecha_fin": hoy().isoformat(), "tipo": "TODAS"}, todas)
        serie = [t for _, t in lecturas_del_dia(sede, hoy())]
        filas.append((SEDES[sede], sede, actual, resumen, semana, serie))
    return filas


if autorizadas:
    st.markdown(ui.seccion("Estado de las cámaras", "termometro"), unsafe_allow_html=True)
    tarjetas = "".join(ui.tarjeta_sede(*fila) for fila in datos_tablero(tuple(autorizadas)))
    st.markdown('<div class="tablero">%s</div>' % tarjetas, unsafe_allow_html=True)


# ============================================================ captura de entrada
entrada = st.chat_input("Escriba su consulta")
pregunta = entrada or estado.pendiente
estado.pendiente = None


# ======================================================== conversación y evidencia
izquierda, derecha = st.columns([1.45, 1], gap="large")

with izquierda:
    st.markdown(ui.seccion("Conversación", "chip"), unsafe_allow_html=True)

    for mensaje in estado.mensajes:
        avatar = AVATAR_ASISTENTE if mensaje["role"] == "assistant" else AVATAR_USUARIO
        with st.chat_message(mensaje["role"], avatar=avatar):
            st.markdown(mensaje["content"])

    if len(estado.mensajes) == 1 and not pregunta:
        columnas = st.columns(2)
        for i, (texto, rotulo) in enumerate(SUGERENCIAS):
            with columnas[i % 2]:
                if st.button("**%s**  \n%s" % (rotulo, texto), key="sug_%d" % i,
                             use_container_width=True):
                    estado.pendiente = texto
                    st.rerun()

    if pregunta:
        if not clave:
            st.error("Falta la clave de %s. Obténgala en %s e ingrésela en la barra lateral."
                     % (datos["variable"], datos["consola"]))
        else:
            estado.mensajes.append({"role": "user", "content": pregunta})
            with st.chat_message("user", avatar=AVATAR_USUARIO):
                st.markdown(pregunta)

            with st.chat_message("assistant", avatar=AVATAR_ASISTENTE):
                with st.spinner("Consultando el monitor"):
                    try:
                        historial = [{"role": m["role"], "content": m["content"]}
                                     for m in estado.mensajes if m["role"] in ("user", "assistant")]
                        salida = responder(crear_cliente(proveedor, clave), proveedor, PROMPT,
                                           historial, autorizadas, modelo=modelo)
                    except Exception as error:
                        salida = None
                        estado.mensajes.pop()
                        st.error("No se pudo completar la consulta. %s" % error)

                if salida:
                    st.markdown(salida["texto"])
                    estado.mensajes.append({
                        "role": "assistant", "content": salida["texto"], "traza": salida["traza"],
                        "huerfanas": salida["huerfanas"], "cache": salida.get("desde_cache", False),
                        "pregunta": pregunta})
                    estado.turno_visible = len(estado.mensajes) - 1


with derecha:
    st.markdown(ui.seccion("Evidencia del turno", "escudo"), unsafe_allow_html=True)

    turnos = [i for i, m in enumerate(estado.mensajes)
              if m["role"] == "assistant" and m.get("pregunta")]

    if not turnos:
        st.markdown(
            '<div class="evid"><div class="evid-vacio">Aquí verá, para cada respuesta, qué funciones '
            'pidió el modelo, con qué parámetros, qué devolvió el monitor y si todas las cifras '
            'tienen respaldo. Es el ciclo <span class="mono">requires_action</span> hecho visible.'
            '</div></div>', unsafe_allow_html=True)
    else:
        if len(turnos) > 1:
            etiquetas = {i: "Turno %d · %s" % (n, estado.mensajes[i]["pregunta"][:46])
                         for n, i in enumerate(turnos, 1)}
            actual = estado.turno_visible if estado.turno_visible in turnos else turnos[-1]
            elegido = st.selectbox("Turno", turnos, index=turnos.index(actual),
                                   format_func=etiquetas.get, label_visibility="collapsed")
        else:
            elegido = turnos[0]

        m = estado.mensajes[elegido]
        st.markdown(ui.linea_de_tiempo(m["traza"], m.get("huerfanas") or set(), SEDES,
                                       m.get("cache", False), m["pregunta"]),
                    unsafe_allow_html=True)

        if m["traza"]:
            with st.expander("Ver contrato JSON de cada llamada", icon=":material/data_object:"):
                for n, paso in enumerate(m["traza"], 1):
                    st.caption("%d · %s" % (n, paso["funcion"]))
                    st.json({"argumentos": paso["argumentos"], "resultado": paso["resultado"]},
                            expanded=False)


st.markdown(ui.pie(RUTA_BITACORA), unsafe_allow_html=True)
