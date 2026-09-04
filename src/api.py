"""
API HTTP del monitor de cadena de frio.
Usa solo la libreria estandar de Python: no requiere instalar dependencias,
lo que hace que la imagen sea pequena y el arranque inmediato.

Endpoints:
  GET  /health              -> estado del servicio
  GET  /clasificar?t=4.5    -> clasifica una lectura individual
  POST /resumen             -> resumen de una jornada (JSON: {"lecturas": [...]})
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from src.monitor import LecturaInvalida, clasificar, resumen

PUERTO = int(os.environ.get("PUERTO", 8000))
SEDE = os.environ.get("SEDE", "sede-desconocida")


class Handler(BaseHTTPRequestHandler):

    def _responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        ruta = urlparse(self.path)

        if ruta.path == "/health":
            return self._responder(200, {
                "estado": "activo",
                "servicio": "monitor-cadena-frio",
                "sede": SEDE,
                "rango_permitido": "2.0 a 8.0 C",
            })

        if ruta.path == "/clasificar":
            params = parse_qs(ruta.query)
            valor = params.get("t", [None])[0]
            try:
                return self._responder(200, {
                    "lectura": float(valor),
                    "estado": clasificar(valor),
                    "sede": SEDE,
                })
            except (LecturaInvalida, TypeError, ValueError):
                return self._responder(400, {"error": "Lectura invalida"})

        return self._responder(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        ruta = urlparse(self.path)
        if ruta.path != "/resumen":
            return self._responder(404, {"error": "Ruta no encontrada"})

        largo = int(self.headers.get("Content-Length", 0))
        try:
            cuerpo = json.loads(self.rfile.read(largo) or b"{}")
            datos = resumen(cuerpo.get("lecturas", []))
            datos["sede"] = SEDE
            return self._responder(200, datos)
        except (LecturaInvalida, json.JSONDecodeError, ValueError):
            return self._responder(400, {"error": "Cuerpo invalido"})

    def log_message(self, formato, *args):
        print("[monitor] %s" % (formato % args))


if __name__ == "__main__":
    print("Monitor de cadena de frio escuchando en el puerto %d" % PUERTO)
    print("Sede configurada: %s" % SEDE)
    HTTPServer(("0.0.0.0", PUERTO), Handler).serve_forever()
