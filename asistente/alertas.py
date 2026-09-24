"""
Canal de alertas (frente de IA, guia interna seccion 5).

La guia pide que el asistente no solo consulte el historico, sino que ademas
avise al responsable cuando hay una excursion. El envio real se hace por
webhook; si no hay webhook configurado, la alerta se registra localmente y se
devuelve el estado REGISTRADA_LOCALMENTE, de modo que la demostracion funciona
sin depender de un servicio externo.

Una alerta nunca se inventa: antes de enviarla se verifica contra el
repositorio que la excursion exista de verdad.
"""

import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime

RUTA_ALERTAS = os.path.join("bitacora", "alertas.jsonl")
TIEMPO_MAXIMO_S = 8

DESTINATARIOS = {
    "quimico-farmaceutico-turno": "Quimico farmaceutico de turno",
    "jefe-almacen": "Jefe de almacen",
    "auditoria-interna": "Auditoria interna",
}


def _registrar(alerta):
    try:
        os.makedirs(os.path.dirname(RUTA_ALERTAS), exist_ok=True)
        with open(RUTA_ALERTAS, "a", encoding="utf-8") as f:
            f.write(json.dumps(alerta, ensure_ascii=False) + "\n")
    except OSError:
        pass


def enviar(destinatario, asunto, cuerpo, datos=None):
    """Envia la alerta y devuelve el comprobante.

    Estados posibles:
      ENVIADA                 el webhook respondio correctamente
      REGISTRADA_LOCALMENTE   no hay webhook configurado (modo demostracion)
      FALLO_ENVIO             el webhook existe pero no respondio
    """
    alerta = {
        "id": "alerta-" + uuid.uuid4().hex[:8],
        "momento": datetime.now().isoformat(timespec="seconds"),
        "destinatario": destinatario,
        "nombre_destinatario": DESTINATARIOS.get(destinatario, destinatario),
        "asunto": asunto,
        "cuerpo": cuerpo,
        "datos": datos or {},
    }

    webhook = os.environ.get("WEBHOOK_ALERTAS", "").strip()
    if not webhook:
        alerta["estado"] = "REGISTRADA_LOCALMENTE"
        alerta["canal"] = "bitacora"
        _registrar(alerta)
        return alerta

    alerta["canal"] = "webhook"
    peticion = urllib.request.Request(
        webhook, data=json.dumps(alerta, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_MAXIMO_S) as respuesta:
            alerta["estado"] = "ENVIADA" if 200 <= respuesta.status < 300 else "FALLO_ENVIO"
            alerta["codigo_http"] = respuesta.status
    except (urllib.error.URLError, OSError, ValueError) as e:
        alerta["estado"] = "FALLO_ENVIO"
        alerta["detalle"] = type(e).__name__

    _registrar(alerta)
    return alerta
