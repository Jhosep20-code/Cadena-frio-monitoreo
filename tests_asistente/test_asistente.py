"""
Pruebas del asistente. No llaman a ninguna API: verifican el repositorio, las
cinco herramientas y la verificacion de procedencia.
"""

from datetime import date, timedelta

import pytest

from asistente.herramientas import ejecutar
from asistente.repositorio import LECTURAS_POR_DIA, SEDES, hoy, lecturas_del_dia
from asistente.verificacion import verificar_procedencia

AMBAS = list(SEDES)
SOLO_HUANCAYO = ["almacen-huancayo"]
AYER = (hoy() - timedelta(days=1)).isoformat()
HOY = hoy().isoformat()
FUTURO = (hoy() + timedelta(days=5)).isoformat()


class TestRepositorio:
    def test_una_jornada_completa_tiene_96_lecturas_menos_las_perdidas(self):
        jauja = lecturas_del_dia("almacen-jauja", hoy() - timedelta(days=1))
        assert len(jauja) == LECTURAS_POR_DIA - 2

    def test_es_determinista(self):
        dia = hoy() - timedelta(days=3)
        assert lecturas_del_dia("almacen-jauja", dia) == lecturas_del_dia("almacen-jauja", dia)

    def test_cada_sede_tiene_su_propia_serie(self):
        dia = hoy() - timedelta(days=3)
        assert lecturas_del_dia("almacen-jauja", dia) != lecturas_del_dia("almacen-huancayo", dia)


class TestResumenJornada:
    def test_jauja_ayer_es_no_conforme(self):
        r = ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": AYER}, AMBAS)
        assert r["estado"] == "NO CONFORME"
        assert r["maxima"] == 9.6
        assert r["lecturas_fuera_de_rango"] == 4
        assert r["cobertura_pct"] == 97.9
        assert r["parcial"] is False

    def test_huancayo_ayer_es_conforme(self):
        r = ejecutar("generar_resumen_jornada", {"sede": "almacen-huancayo", "fecha": AYER}, AMBAS)
        assert r["estado"] == "CONFORME"
        assert r["lecturas_fuera_de_rango"] == 0
        assert r["cobertura_pct"] == 100.0

    def test_la_jornada_de_hoy_se_marca_parcial(self):
        r = ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": HOY}, AMBAS)
        assert r["parcial"] is True

    def test_fecha_futura_se_rechaza(self):
        r = ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": FUTURO}, AMBAS)
        assert r["error"] == "FECHA_INVALIDA"

    def test_fecha_con_formato_equivocado(self):
        r = ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": "20/09/2026"}, AMBAS)
        assert r["error"] == "FECHA_INVALIDA"


class TestControlDeAcceso:
    def test_sede_no_autorizada_no_devuelve_datos(self):
        r = ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": AYER}, SOLO_HUANCAYO)
        assert r["error"] == "ACCESO_DENEGADO"
        assert "maxima" not in r and "estado" not in r

    def test_sede_inexistente(self):
        r = ejecutar("consultar_temperatura_actual", {"sede": "almacen-lima"}, AMBAS)
        assert r["error"] in ("FECHA_INVALIDA", "ACCESO_DENEGADO")

    def test_listar_solo_muestra_las_autorizadas(self):
        r = ejecutar("listar_sedes_autorizadas", {}, SOLO_HUANCAYO)
        assert [s["id"] for s in r["sedes"]] == SOLO_HUANCAYO


class TestExcursiones:
    def test_cuatro_lecturas_seguidas_son_un_solo_episodio(self):
        r = ejecutar("consultar_excursiones_termicas",
                     {"sede": "almacen-jauja", "fecha_inicio": AYER, "fecha_fin": AYER,
                      "tipo": "TODAS"}, AMBAS)
        assert r["total_episodios"] == 1
        episodio = r["episodios"][0]
        assert episodio["lecturas_fuera_de_rango"] == 4
        assert episodio["tipo"] == "ALERTA_ALTA"
        assert episodio["valor_extremo"] == 9.6
        assert episodio["duracion_estimada_min"] == 60
        assert episodio["inicio"].endswith("03:15") and episodio["fin"].endswith("04:00")

    def test_filtrar_por_tipo_descarta_las_altas(self):
        r = ejecutar("consultar_excursiones_termicas",
                     {"sede": "almacen-jauja", "fecha_inicio": AYER, "fecha_fin": AYER,
                      "tipo": "ALERTA_BAJA"}, AMBAS)
        assert r["total_episodios"] == 0

    def test_huancayo_tuvo_una_alerta_baja_hace_cuatro_dias(self):
        desde = (hoy() - timedelta(days=6)).isoformat()
        r = ejecutar("consultar_excursiones_termicas",
                     {"sede": "almacen-huancayo", "fecha_inicio": desde,
                      "fecha_fin": hoy().isoformat(), "tipo": "TODAS"}, AMBAS)
        assert r["total_episodios"] == 1
        assert r["episodios"][0]["tipo"] == "ALERTA_BAJA"
        assert r["episodios"][0]["valor_extremo"] == 1.4

    def test_periodo_mayor_a_31_dias_se_rechaza(self):
        desde = (hoy() - timedelta(days=40)).isoformat()
        r = ejecutar("consultar_excursiones_termicas",
                     {"sede": "almacen-jauja", "fecha_inicio": desde,
                      "fecha_fin": hoy().isoformat(), "tipo": "TODAS"}, AMBAS)
        assert r["error"] == "PERIODO_EXCEDIDO"


class TestLecturasPeriodo:
    def test_devuelve_la_ventana_pedida(self):
        r = ejecutar("consultar_lecturas_periodo",
                     {"sede": "almacen-jauja", "desde": AYER + "T03:00",
                      "hasta": AYER + "T04:30", "solo_alertas": False}, AMBAS)
        assert r["total"] == 7
        assert r["lecturas"][0] == {"hora": "03:00", "t": r["lecturas"][0]["t"], "estado": "OK"}

    def test_filtro_de_alertas(self):
        r = ejecutar("consultar_lecturas_periodo",
                     {"sede": "almacen-jauja", "desde": AYER + "T00:00",
                      "hasta": AYER + "T23:45", "solo_alertas": True}, AMBAS)
        assert r["total"] == 4
        assert all(l["estado"] != "OK" for l in r["lecturas"])

    def test_ventana_mayor_a_24_horas(self):
        r = ejecutar("consultar_lecturas_periodo",
                     {"sede": "almacen-jauja", "desde": AYER + "T00:00",
                      "hasta": HOY + "T23:45", "solo_alertas": False}, AMBAS)
        assert r["error"] == "PERIODO_EXCEDIDO"


class TestTemperaturaActual:
    def test_devuelve_estado_y_antiguedad(self):
        r = ejecutar("consultar_temperatura_actual", {"sede": "almacen-huancayo"}, AMBAS)
        assert r["estado"] in ("OK", "ALERTA_ALTA", "ALERTA_BAJA")
        assert r["antiguedad_min"] >= 0
        assert r["unidad"] == "C"


class TestVerificacionDeProcedencia:
    RESULTADOS = [{"maxima": 9.6, "minima": 3.6, "total_lecturas": 94, "cobertura_pct": 97.9}]

    def test_respuesta_respaldada_no_tiene_huerfanas(self):
        texto = "La máxima fue 9.6 °C y la mínima 3.6 °C sobre 94 lecturas (97.9 %)."
        _, huerfanas = verificar_procedencia(texto, self.RESULTADOS)
        assert huerfanas == set()

    def test_detecta_una_cifra_inventada(self):
        texto = "La máxima fue 9.2 °C."
        _, huerfanas = verificar_procedencia(texto, self.RESULTADOS)
        assert huerfanas == {"9.2"}

    def test_sin_resultados_no_marca_nada(self):
        _, huerfanas = verificar_procedencia("Hola, ¿en qué puedo ayudarle?", [])
        assert huerfanas == set()


class TestFuncionDesconocida:
    def test_no_lanza_excepcion(self):
        r = ejecutar("borrar_lecturas", {"sede": "almacen-jauja"}, AMBAS)
        assert r["error"] == "FALLO_INTERNO"


# ---------------------------------------------- ciclo del agente (sin red)
class _Funcion:
    def __init__(self, nombre, argumentos):
        self.name, self.arguments = nombre, argumentos


class _Llamada:
    def __init__(self, id, nombre, argumentos):
        self.id, self.type, self.function = id, "function", _Funcion(nombre, argumentos)

    def model_dump(self):
        return {"id": self.id, "type": "function",
                "function": {"name": self.function.name, "arguments": self.function.arguments}}


class _Mensaje:
    def __init__(self, content=None, tool_calls=None):
        self.content, self.tool_calls = content, tool_calls


class _Respuesta:
    def __init__(self, mensaje):
        self.choices = [type("O", (), {"message": mensaje})]


class ClienteFalso:
    """Primero pide dos funciones en paralelo; luego redacta la respuesta."""

    def __init__(self, turnos):
        self.turnos, self.llamadas, self.mensajes_vistos = turnos, 0, []
        self.chat = self
        self.completions = self

    def create(self, model, messages, **kwargs):
        self.mensajes_vistos.append(messages)
        mensaje = self.turnos[self.llamadas]
        self.llamadas += 1
        return _Respuesta(mensaje)


class TestCicloDelAgente:
    def _cliente(self, texto_final):
        return ClienteFalso([
            _Mensaje(tool_calls=[
                _Llamada("call_01", "generar_resumen_jornada",
                         '{"sede":"almacen-jauja","fecha":"%s"}' % AYER),
                _Llamada("call_02", "consultar_excursiones_termicas",
                         '{"sede":"almacen-jauja","fecha_inicio":"%s","fecha_fin":"%s","tipo":"TODAS"}' % (AYER, AYER)),
            ]),
            _Mensaje(content=texto_final),
        ])

    def test_ejecuta_las_funciones_pedidas_y_devuelve_la_traza(self):
        from asistente.agente import responder

        cliente = self._cliente("La jornada fue NO CONFORME: 1 episodio, pico de 9.6 C.")
        salida = responder(cliente, "groq", "prompt", [{"role": "user", "content": "¿y ayer?"}], AMBAS)

        assert [p["funcion"] for p in salida["traza"]] == [
            "generar_resumen_jornada", "consultar_excursiones_termicas"]
        assert salida["traza"][0]["resultado"]["estado"] == "NO CONFORME"
        assert salida["huerfanas"] == set()
        assert "NO CONFORME" in salida["texto"]

    def test_los_resultados_vuelven_al_modelo_como_mensajes_tool(self):
        from asistente.agente import responder

        cliente = self._cliente("Listo.")
        responder(cliente, "groq", "prompt", [{"role": "user", "content": "x"}], AMBAS)

        segunda_llamada = cliente.mensajes_vistos[1]
        roles = [m["role"] for m in segunda_llamada]
        assert roles.count("tool") == 2
        assert segunda_llamada[-1]["tool_call_id"] == "call_02"

    def test_marca_las_cifras_sin_respaldo(self):
        from asistente.agente import responder

        cliente = self._cliente("El pico fue de 9.2 C.")
        salida = responder(cliente, "groq", "prompt", [{"role": "user", "content": "x"}], AMBAS)
        assert salida["huerfanas"] == {"9.2"}

    def test_corta_si_el_modelo_pide_demasiadas_funciones(self):
        from asistente.agente import MAX_RONDAS, responder

        bucle = [_Mensaje(tool_calls=[_Llamada("c%d" % i, "listar_sedes_autorizadas", "{}")])
                 for i in range(MAX_RONDAS + 2)]
        salida = responder(ClienteFalso(bucle), "groq", "prompt",
                           [{"role": "user", "content": "x"}], AMBAS)
        assert "acotarla" in salida["texto"]
        assert len(salida["traza"]) <= MAX_RONDAS

    def test_groq_recibe_los_esquemas_sin_strict(self):
        from asistente.agente import esquemas_para

        assert all("strict" not in e["function"] for e in esquemas_para("groq"))
        assert all(e["function"]["strict"] for e in esquemas_para("openai"))


# ------------------------------------------------- canal de alertas (TA2)
class TestAlertas:
    def _motivo(self):
        return "Excursion alta en Jauja de 03:15 a 04:00, pico de 9.6 C."

    def test_envia_la_alerta_cuando_la_excursion_existe(self, tmp_path, monkeypatch):
        import asistente.alertas as alertas
        monkeypatch.setattr(alertas, "RUTA_ALERTAS", str(tmp_path / "alertas.jsonl"))
        monkeypatch.delenv("WEBHOOK_ALERTAS", raising=False)

        r = ejecutar("notificar_responsable",
                     {"sede": "almacen-jauja", "fecha": AYER,
                      "destinatario": "quimico-farmaceutico-turno", "motivo": self._motivo()}, AMBAS)

        assert r["estado"] == "REGISTRADA_LOCALMENTE"
        assert r["alerta_id"].startswith("alerta-")
        assert r["valor_extremo"] == 9.6
        assert (tmp_path / "alertas.jsonl").read_text(encoding="utf-8").count("\n") == 1

    def test_no_alerta_si_no_hubo_excursion(self):
        r = ejecutar("notificar_responsable",
                     {"sede": "almacen-huancayo", "fecha": AYER,
                      "destinatario": "jefe-almacen", "motivo": "prueba"}, AMBAS)
        assert r["error"] == "SIN_EXCURSION"

    def test_no_alerta_sobre_una_sede_no_autorizada(self):
        r = ejecutar("notificar_responsable",
                     {"sede": "almacen-jauja", "fecha": AYER,
                      "destinatario": "jefe-almacen", "motivo": "prueba"}, SOLO_HUANCAYO)
        assert r["error"] == "ACCESO_DENEGADO"

    def test_destinatario_invalido(self):
        r = ejecutar("notificar_responsable",
                     {"sede": "almacen-jauja", "fecha": AYER,
                      "destinatario": "prensa", "motivo": "prueba"}, AMBAS)
        assert "error" in r

    def test_webhook_caido_no_rompe_la_respuesta(self, tmp_path, monkeypatch):
        import asistente.alertas as alertas
        monkeypatch.setattr(alertas, "RUTA_ALERTAS", str(tmp_path / "a.jsonl"))
        monkeypatch.setenv("WEBHOOK_ALERTAS", "http://127.0.0.1:9/no-existe")

        r = ejecutar("notificar_responsable",
                     {"sede": "almacen-jauja", "fecha": AYER,
                      "destinatario": "auditoria-interna", "motivo": self._motivo()}, AMBAS)
        assert r["estado"] == "FALLO_ENVIO"


class TestEsquemas:
    def test_hay_seis_herramientas_declaradas(self):
        from asistente.herramientas import cargar_esquemas
        from asistente.herramientas import EJECUTORES

        nombres = [e["function"]["name"] for e in cargar_esquemas()]
        assert len(nombres) == 6
        assert set(nombres) == set(EJECUTORES)

    def test_todo_esquema_cumple_el_modo_estricto(self):
        from asistente.herramientas import cargar_esquemas

        for e in cargar_esquemas():
            p = e["function"]["parameters"]
            assert set(p["required"]) == set(p["properties"])
            assert p["additionalProperties"] is False


class TestCacheDeRespuestas:
    """La guia interna pide cachear respuestas en desarrollo para no gastar cuota."""

    def _cliente(self):
        return ClienteFalso([_Mensaje(content="La jornada fue CONFORME.")])

    def test_la_segunda_pregunta_igual_no_llama_al_modelo(self, monkeypatch, tmp_path):
        import asistente.agente as agente

        monkeypatch.setattr(agente, "CACHE_ACTIVA", True)
        monkeypatch.setattr(agente, "RUTA_CACHE", str(tmp_path / "cache.json"))
        historial = [{"role": "user", "content": "¿cómo fue ayer?"}]

        primero = self._cliente()
        a = agente.responder(primero, "groq", "prompt", historial, AMBAS)
        segundo = self._cliente()
        b = agente.responder(segundo, "groq", "prompt", historial, AMBAS)

        assert primero.llamadas == 1 and segundo.llamadas == 0
        assert a["desde_cache"] is False and b["desde_cache"] is True
        assert a["texto"] == b["texto"]

    def test_una_pregunta_distinta_no_usa_la_cache(self, monkeypatch, tmp_path):
        import asistente.agente as agente

        monkeypatch.setattr(agente, "CACHE_ACTIVA", True)
        monkeypatch.setattr(agente, "RUTA_CACHE", str(tmp_path / "cache.json"))

        agente.responder(self._cliente(), "groq", "prompt",
                         [{"role": "user", "content": "uno"}], AMBAS)
        cliente = self._cliente()
        agente.responder(cliente, "groq", "prompt", [{"role": "user", "content": "dos"}], AMBAS)
        assert cliente.llamadas == 1


class TestProveedores:
    def test_los_tres_proveedores_estan_declarados(self):
        from asistente.agente import PROVEEDORES

        assert set(PROVEEDORES) == {"gemini", "groq", "openai"}
        for datos in PROVEEDORES.values():
            assert datos["variable"] and datos["modelo"] and datos["consola"]

    def test_solo_openai_recibe_el_modo_estricto(self):
        from asistente.agente import esquemas_para

        for proveedor in ("gemini", "groq"):
            assert all("strict" not in e["function"] for e in esquemas_para(proveedor))
        assert all(e["function"]["strict"] for e in esquemas_para("openai"))

    def test_gemini_apunta_al_endpoint_compatible(self):
        from asistente.agente import PROVEEDORES

        assert PROVEEDORES["gemini"]["base_url"].endswith("/openai/")

    def test_se_puede_usar_un_modelo_distinto_al_por_defecto(self):
        from asistente.agente import responder

        cliente = ClienteFalso([_Mensaje(content="listo")])
        responder(cliente, "gemini", "prompt", [{"role": "user", "content": "x"}],
                  AMBAS, modelo="gemini-3.5-flash")
        assert cliente.mensajes_vistos  # la llamada se hizo con el modelo indicado

    def test_modelos_disponibles_no_lanza_si_falla(self):
        from asistente.agente import modelos_disponibles

        class Roto:
            @property
            def models(self):
                raise RuntimeError("sin red")

        assert modelos_disponibles(Roto())[0].startswith("No se pudo consultar")


# ------------------------------------------------ componentes visuales (ui)
class TestInterfaz:
    SEDES = {"almacen-jauja": "Almacen Jauja", "almacen-huancayo": "Almacen Huancayo"}

    def _resumen(self):
        return ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": AYER}, AMBAS)

    def _excursiones(self):
        return ejecutar("consultar_excursiones_termicas",
                        {"sede": "almacen-jauja", "fecha_inicio": AYER, "fecha_fin": AYER,
                         "tipo": "TODAS"}, AMBAS)

    def test_no_usa_emojis(self):
        import re
        from asistente import ui
        todo = ui.ESTILOS + ui.cabecera("x", "m", "p") + ui.icono("alerta")
        assert not re.search("[\U0001F300-\U0001FAFF\u2600-\u27BF]", todo)

    def test_iconos_son_svg_de_linea(self):
        from asistente import ui
        for nombre in ("termometro", "alerta", "campana", "bloqueo", "inexistente"):
            assert ui.icono(nombre).startswith("<svg")
            assert 'stroke="currentColor"' in ui.icono(nombre)

    def test_tarjeta_de_sede_muestra_estado_y_grafico(self):
        from asistente import ui
        actual = ejecutar("consultar_temperatura_actual", {"sede": "almacen-jauja"}, AMBAS)
        hoy_res = ejecutar("generar_resumen_jornada", {"sede": "almacen-jauja", "fecha": HOY}, AMBAS)
        html = ui.tarjeta_sede("Almacen Jauja", "almacen-jauja", actual, hoy_res,
                               self._excursiones(), [4.0, 5.0, 9.6, 1.4, 4.2])
        assert 'class="sede"' in html and "<polyline" in html
        assert html.count("<circle") == 2          # un punto rojo (9.6) y uno azul (1.4)

    def test_tarjeta_sin_datos(self):
        from asistente import ui
        html = ui.tarjeta_sede("X", "x", {"error": "SIN_DATOS", "mensaje": "nada"}, {}, {}, [])
        assert "Sin datos" in html

    def test_grafico_necesita_al_menos_dos_puntos(self):
        from asistente import ui
        assert ui.grafico([4.5]) == ""

    def test_linea_de_tiempo_con_todos_los_tipos_de_resultado(self):
        from asistente import ui
        actual = ejecutar("consultar_temperatura_actual", {"sede": "almacen-huancayo"}, AMBAS)
        lecturas = ejecutar("consultar_lecturas_periodo",
                            {"sede": "almacen-jauja", "desde": AYER + "T00:00",
                             "hasta": AYER + "T23:45", "solo_alertas": False}, AMBAS)
        traza = [
            {"ronda": 1, "funcion": "generar_resumen_jornada", "ms": 1,
             "argumentos": {"sede": "almacen-jauja", "fecha": AYER}, "resultado": self._resumen()},
            {"ronda": 1, "funcion": "consultar_excursiones_termicas", "ms": 1,
             "argumentos": {"sede": "almacen-jauja"}, "resultado": self._excursiones()},
            {"ronda": 2, "funcion": "consultar_temperatura_actual", "ms": 1,
             "argumentos": {"sede": "almacen-huancayo"}, "resultado": actual},
            {"ronda": 2, "funcion": "consultar_lecturas_periodo", "ms": 1,
             "argumentos": {"motivo": "x" * 80}, "resultado": lecturas},
            {"ronda": 3, "funcion": "listar_sedes_autorizadas", "ms": 0, "argumentos": {},
             "resultado": {"sedes": [{"id": "almacen-jauja", "nombre": "Almacen Jauja"}]}},
            {"ronda": 3, "funcion": "notificar_responsable", "ms": 9, "argumentos": {},
             "resultado": {"alerta_id": "alerta-1", "estado": "REGISTRADA_LOCALMENTE",
                           "destinatario": "QF", "canal": "bitacora"}},
            {"ronda": 3, "funcion": "generar_resumen_jornada", "ms": 0,
             "argumentos": {"sede": "almacen-lima"},
             "resultado": {"error": "ACCESO_DENEGADO", "mensaje": "sin acceso"}},
            {"ronda": 3, "funcion": "otra", "ms": 0, "argumentos": {}, "resultado": {"a": 1}},
        ]
        html = ui.linea_de_tiempo(traza, set(), self.SEDES, desde_cache=True, pregunta="¿y?")
        for marca in ("NO CONFORME", "1 episodio", "ACCESO_DENEGADO", "alerta-1",
                      "Verificación de procedencia", "desde caché", "3 ronda(s)", "…"):
            assert marca in html, marca

    def test_linea_de_tiempo_marca_cifras_huerfanas(self):
        from asistente import ui
        traza = [{"ronda": 1, "funcion": "generar_resumen_jornada", "ms": 1,
                  "argumentos": {}, "resultado": self._resumen()}]
        assert "sin respaldo" in ui.linea_de_tiempo(traza, {"9.2"}, self.SEDES)

    def test_turno_sin_herramientas(self):
        from asistente import ui
        assert "sin consultar datos nuevos" in ui.linea_de_tiempo([], set(), self.SEDES)

    def test_excursiones_vacias_y_pie(self):
        from asistente import ui
        vacio = ejecutar("consultar_excursiones_termicas",
                         {"sede": "almacen-huancayo", "fecha_inicio": AYER, "fecha_fin": AYER,
                          "tipo": "TODAS"}, AMBAS)
        traza = [{"ronda": 1, "funcion": "consultar_excursiones_termicas", "ms": 1,
                  "argumentos": {}, "resultado": vacio}]
        assert "Sin episodios" in ui.linea_de_tiempo(traza, set(), self.SEDES)
        assert "bitacora" in ui.pie("bitacora/x.jsonl")
        assert "Estado" in ui.seccion("Estado", "chip")
