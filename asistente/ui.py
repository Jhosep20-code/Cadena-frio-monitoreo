"""
Componentes visuales de Termo.

Todo lo que es presentacion vive aqui: la hoja de estilos, los iconos de linea
en SVG, las tarjetas del tablero, el grafico de lecturas y la linea de tiempo
del ciclo de herramientas. app.py solo decide QUE mostrar; este modulo decide
COMO se ve.

Cada funcion devuelve HTML como texto, de modo que se puede probar sin levantar
Streamlit.
"""

from html import escape

# ------------------------------------------------------------------ paleta
TINTA = "#0A1020"
PANEL = "#0F1830"
HIELO = "#38BDF8"
HIELO_SUAVE = "rgba(56, 189, 248, .10)"
ROJO = "#E11D48"
AMBAR = "#F59E0B"
VERDE = "#10B981"
TEXTO = "#E6EDF6"
TENUE = "#8A9BB4"
LINEA = "rgba(148, 163, 184, .16)"

# ---------------------------------------------------- iconos de linea (24px)
_TRAZO = ('<svg xmlns="http://www.w3.org/2000/svg" width="{t}" height="{t}" viewBox="0 0 24 24" '
          'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true">{p}</svg>')

_RUTAS = {
    "termometro": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "copo": '<path d="M12 2v20M4.9 6.5l14.2 11M4.9 17.5l14.2-11"/><path d="m9 4 3 2 3-2M9 20l3-2 3 2"/>',
    "alerta": '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z"/><path d="M12 9v4M12 17h.01"/>',
    "escudo": '<path d="M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1Z"/><path d="m9 12 2 2 4-4"/>',
    "campana": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
    "reloj": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "base": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "bloqueo": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "chip": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
    "pregunta": '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
    "lista": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "verificado": '<path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/><path d="m9 11 3 3L22 4"/>',
    "tendencia": '<path d="M22 7 13.5 15.5 8.5 10.5 2 17"/><path d="M16 7h6v6"/>',
    "sede": '<path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/><path d="M9 9v.01M9 12v.01M9 15v.01M9 18v.01"/>',
}


def icono(nombre, tamano=18):
    return _TRAZO.format(t=tamano, p=_RUTAS.get(nombre, _RUTAS["chip"]))


ICONO_FUNCION = {
    "listar_sedes_autorizadas": "lista",
    "consultar_temperatura_actual": "termometro",
    "consultar_lecturas_periodo": "tendencia",
    "consultar_excursiones_termicas": "alerta",
    "generar_resumen_jornada": "base",
    "notificar_responsable": "campana",
}

TITULO_FUNCION = {
    "listar_sedes_autorizadas": "Sedes autorizadas",
    "consultar_temperatura_actual": "Temperatura actual",
    "consultar_lecturas_periodo": "Lecturas del periodo",
    "consultar_excursiones_termicas": "Excursiones térmicas",
    "generar_resumen_jornada": "Resumen de jornada",
    "notificar_responsable": "Envío de alerta",
}

# ------------------------------------------------------------ hoja de estilos
ESTILOS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --tinta: #0A1020; --panel: #0F1830; --panel-2: #131F3B;
  --hielo: #38BDF8; --hielo-suave: rgba(56,189,248,.10);
  --rojo: #E11D48; --ambar: #F59E0B; --verde: #10B981;
  --texto: #E6EDF6; --tenue: #8A9BB4; --linea: rgba(148,163,184,.16);
  --radio: 14px;
}

/* Tipografia solo en texto: nunca sobre los iconos Material, que usan su propia fuente */
html, body, .stMarkdown, p, li, label, input, textarea, h1, h2, h3, h4,
div[data-testid="stChatMessageContent"], div[data-testid="stCaptionContainer"],
div[data-baseweb="select"], button p {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}
span[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {
  font-family: 'Material Symbols Rounded' !important;
}
code, pre, .mono { font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace !important; }

/* Lienzo */
.stApp { background:
  radial-gradient(1200px 500px at 85% -10%, rgba(56,189,248,.10), transparent 60%),
  radial-gradient(900px 400px at -10% 110%, rgba(225,29,72,.06), transparent 60%),
  var(--tinta); }
.block-container { padding-top: 3.4rem !important; padding-bottom: 7rem !important; max-width: 1480px; }
header[data-testid="stHeader"] { background: transparent; }
footer, #MainMenu { visibility: hidden; }

/* Barra lateral */
section[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--linea); }
section[data-testid="stSidebar"] .stMarkdown h4 {
  font-size: .70rem; letter-spacing: .14em; text-transform: uppercase;
  color: var(--tenue); margin: 1.1rem 0 .4rem; font-weight: 600; }

/* Cabecera */
.cab { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom: 18px; }
.cab-marca { display:flex; align-items:center; gap:14px; }
.cab-marca img { width:46px; height:46px; }
.cab-marca h1 { font-size: 1.55rem !important; font-weight:700 !important; margin:0 !important; padding:0 !important; letter-spacing:-.02em; }
.cab-marca p { margin:2px 0 0; color: var(--tenue); font-size:.82rem; }
.cab-estado { display:flex; gap:8px; flex-wrap:wrap; }
.pill { display:inline-flex; align-items:center; gap:6px; padding:5px 11px; border-radius:999px;
  font-size:.74rem; color: var(--texto); background: var(--panel-2); border:1px solid var(--linea); white-space:nowrap; }
.pill svg { color: var(--hielo); }
.pill .punto { width:7px; height:7px; border-radius:50%; background: var(--verde); box-shadow: 0 0 0 3px rgba(16,185,129,.18); }

/* Tablero de sedes */
.tablero { display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:14px; margin-bottom: 22px; }
.sede { background: linear-gradient(180deg, var(--panel-2), var(--panel)); border:1px solid var(--linea);
  border-radius: var(--radio); padding: 16px 18px 14px; position:relative; overflow:hidden; }
.sede::before { content:""; position:absolute; inset:0 0 auto 0; height:3px; background: var(--acento, var(--hielo)); }
.sede-top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
.sede-nombre { display:flex; align-items:center; gap:8px; font-weight:600; font-size:.92rem; }
.sede-nombre svg { color: var(--tenue); }
.sede-id { color: var(--tenue); font-size:.72rem; margin-top:2px; }
.estado { font-size:.68rem; font-weight:700; letter-spacing:.08em; padding:4px 9px; border-radius:6px; text-transform:uppercase; }
.estado.ok { color:#6EE7B7; background: rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.35); }
.estado.alta { color:#FDA4AF; background: rgba(225,29,72,.12); border:1px solid rgba(225,29,72,.40); }
.estado.baja { color:#93C5FD; background: rgba(59,130,246,.12); border:1px solid rgba(59,130,246,.40); }
.sede-cifra { display:flex; align-items:baseline; gap:6px; margin:10px 0 2px; }
.sede-cifra b { font-size:2.35rem; font-weight:700; letter-spacing:-.03em; line-height:1; }
.sede-cifra span { color: var(--tenue); font-size:.95rem; }
.sede-sub { color: var(--tenue); font-size:.74rem; }
.sede svg.graf { width:100%; height:64px; display:block; margin:10px 0 8px; }
.sede-pie { display:grid; grid-template-columns: 1fr 1fr; gap:8px; border-top:1px solid var(--linea); padding-top:10px; }
.sede-pie div { font-size:.72rem; color: var(--tenue); }
.sede-pie strong { display:block; color: var(--texto); font-size:.84rem; font-weight:600; margin-top:2px; }

/* Titulos de seccion */
.seccion { display:flex; align-items:center; gap:8px; font-size:.70rem; letter-spacing:.14em; text-transform:uppercase;
  color: var(--tenue); font-weight:600; margin: 4px 0 12px; }
.seccion svg { color: var(--hielo); }

/* Conversacion */
div[data-testid="stChatMessage"] { background: transparent !important; padding: .35rem 0 !important; }
div[data-testid="stChatMessageContent"] { font-size: .93rem; line-height: 1.6; }
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
  background: var(--panel-2); border:1px solid var(--linea); border-radius: 12px; padding: 8px 14px; }
div[data-testid="stChatMessageAvatarAssistant"], div[data-testid="stChatMessageAvatarUser"] {
  background: var(--hielo-suave) !important; color: var(--hielo) !important; border:1px solid var(--linea); }
div[data-testid="stChatInput"] { border-radius: 14px !important; }
div[data-testid="stChatInput"] textarea { font-size: .92rem !important; }

/* Tarjetas de sugerencia */
div.stButton > button { background: var(--panel); border:1px solid var(--linea); border-radius: 12px;
  color: var(--texto); text-align:left; justify-content:flex-start; padding: 10px 14px; font-size:.84rem;
  transition: border-color .15s, transform .15s; }
div.stButton > button:hover { border-color: var(--hielo); color: var(--texto); transform: translateY(-1px); }
div.stButton > button p { white-space: normal !important; text-align: left; line-height: 1.45; margin: 0; }
div.stButton > button strong { color: var(--hielo); font-size: .70rem; letter-spacing: .10em;
  text-transform: uppercase; font-weight: 600; display: block; margin-bottom: 3px; }

/* Panel de evidencia: linea de tiempo */
.evid { background: var(--panel); border:1px solid var(--linea); border-radius: var(--radio); padding: 16px 16px 6px; }
.evid-vacio { color: var(--tenue); font-size:.84rem; line-height:1.55; padding: 4px 2px 10px; }
.evid-meta { display:flex; gap:6px; flex-wrap:wrap; margin-bottom: 14px; }
.tl { position:relative; padding-left: 30px; }
.tl::before { content:""; position:absolute; left: 11px; top: 6px; bottom: 6px; width:2px; background: var(--linea); }
.nodo { position:relative; margin-bottom: 18px; }
.nodo-ico { position:absolute; left:-30px; top:0; width:24px; height:24px; border-radius:50%;
  display:flex; align-items:center; justify-content:center; background: var(--panel-2);
  border:1px solid var(--hielo); color: var(--hielo); }
.nodo.falla .nodo-ico { border-color: var(--rojo); color: var(--rojo); }
.nodo.envio .nodo-ico { border-color: var(--ambar); color: var(--ambar); }
.nodo.fin .nodo-ico { border-color: var(--verde); color: var(--verde); }
.nodo-tit { font-weight:600; font-size:.86rem; display:flex; justify-content:space-between; gap:8px; }
.nodo-tit small { color: var(--tenue); font-weight:500; font-size:.70rem; white-space:nowrap; }
.nodo-fn { font-size:.70rem; color: var(--tenue); margin: 1px 0 8px; }
.args { display:flex; flex-wrap:wrap; gap:5px; margin-bottom: 8px; }
.arg { font-size:.70rem; padding:3px 8px; border-radius:6px; background: var(--hielo-suave); border:1px solid var(--linea); }
.arg b { color: var(--hielo); font-weight:600; margin-right:4px; }
.res { background: var(--panel-2); border:1px solid var(--linea); border-radius:10px; padding: 10px 12px; }
.res.error { border-color: rgba(225,29,72,.45); background: rgba(225,29,72,.07); }
.res-err { color:#FDA4AF; font-size:.80rem; }
.res-err b { display:block; font-family:'JetBrains Mono', monospace; font-size:.74rem; margin-bottom:2px; }
.kpis { display:grid; grid-template-columns: repeat(auto-fit, minmax(92px, 1fr)); gap:8px; }
.kpi span { display:block; font-size:.64rem; letter-spacing:.08em; text-transform:uppercase; color: var(--tenue); }
.kpi b { font-size:1.02rem; font-weight:700; }
.veredicto { display:inline-block; font-size:.70rem; font-weight:700; letter-spacing:.08em; padding:3px 9px;
  border-radius:6px; margin-bottom:8px; }
.veredicto.ok { color:#6EE7B7; background: rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.35); }
.veredicto.no { color:#FDA4AF; background: rgba(225,29,72,.12); border:1px solid rgba(225,29,72,.40); }
.tabla { width:100%; border-collapse: collapse; font-size:.74rem; }
.tabla th { text-align:left; color: var(--tenue); font-weight:600; font-size:.62rem; letter-spacing:.08em;
  text-transform:uppercase; padding: 0 6px 6px 0; border-bottom:1px solid var(--linea); }
.tabla td { padding: 6px 6px 6px 0; border-bottom:1px solid var(--linea); white-space:nowrap; }
.tabla tr:last-child td { border-bottom:none; }
.t-alta { color:#FDA4AF; } .t-baja { color:#93C5FD; }
.sello-fin { display:flex; align-items:center; gap:8px; font-size:.78rem; padding: 10px 12px; border-radius:10px; margin: 2px 0 12px; }
.sello-fin.ok { color:#6EE7B7; background: rgba(16,185,129,.08); border:1px solid rgba(16,185,129,.30); }
.sello-fin.no { color:#FDA4AF; background: rgba(225,29,72,.08); border:1px solid rgba(225,29,72,.35); }

/* Pie */
.pie { color: var(--tenue); font-size:.72rem; border-top:1px solid var(--linea); padding-top:12px; margin-top: 18px; line-height:1.6; }

/* Responsivo */
@media (max-width: 900px) {
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
  .sede-cifra b { font-size: 2rem; }
}
@media (max-width: 560px) {
  .cab-estado { width:100%; }
  .tablero { grid-template-columns: 1fr; }
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .tabla { font-size:.68rem; }
}
</style>
"""


# ------------------------------------------------------------ utilidades
def _t(valor):
    return "%.1f&nbsp;°C" % valor


def _hora(iso):
    return iso.split("T")[-1] if "T" in iso else iso


def _fecha_corta(iso):
    """2026-09-22 -> 22/09"""
    partes = iso.split("T")[0].split("-")
    return "%s/%s" % (partes[2], partes[1]) if len(partes) == 3 else iso


def estado_css(estado):
    return {"OK": "ok", "ALERTA_ALTA": "alta", "ALERTA_BAJA": "baja"}.get(estado, "ok")


def estado_texto(estado):
    return {"OK": "En rango", "ALERTA_ALTA": "Alerta alta", "ALERTA_BAJA": "Alerta baja"}.get(estado, estado)


# ------------------------------------------------------------ componentes
def cabecera(logo_b64, modelo, proveedor):
    return (
        '<div class="cab"><div class="cab-marca">'
        '<img src="data:image/svg+xml;base64,%s" alt="Termo"/>'
        '<div><h1>Termo</h1><p>Monitor de cadena de frío · rango permitido 2.0 – 8.0 °C</p></div></div>'
        '<div class="cab-estado">'
        '<span class="pill"><span class="punto"></span>Monitor en línea</span>'
        '<span class="pill">%s%s</span>'
        '<span class="pill">%sCifras calculadas por monitor.py</span>'
        '</div></div>'
    ) % (logo_b64, icono("chip", 14), escape("%s · %s" % (proveedor, modelo)), icono("escudo", 14))


def grafico(lecturas, ancho=300, alto=64):
    """Serie del dia con la banda permitida de 2 a 8 C sombreada."""
    if len(lecturas) < 2:
        return ""
    minimo, maximo = 0.0, 11.0
    y = lambda v: alto - (min(max(v, minimo), maximo) - minimo) / (maximo - minimo) * alto
    paso = ancho / (len(lecturas) - 1)
    puntos = " ".join("%.1f,%.1f" % (i * paso, y(v)) for i, v in enumerate(lecturas))
    fuera = "".join(
        '<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s"/>' % (i * paso, y(v), ROJO if v > 8 else "#3B82F6")
        for i, v in enumerate(lecturas) if v > 8 or v < 2)
    return (
        '<svg class="graf" viewBox="0 0 %d %d" preserveAspectRatio="none" role="img" '
        'aria-label="Lecturas de hoy">'
        '<rect x="0" y="%.1f" width="%d" height="%.1f" fill="%s"/>'
        '<line x1="0" x2="%d" y1="%.1f" y2="%.1f" stroke="%s" stroke-dasharray="3 4" stroke-width="1"/>'
        '<line x1="0" x2="%d" y1="%.1f" y2="%.1f" stroke="%s" stroke-dasharray="3 4" stroke-width="1"/>'
        '<polyline points="%s" fill="none" stroke="%s" stroke-width="1.8" '
        'stroke-linejoin="round" vector-effect="non-scaling-stroke"/>%s</svg>'
    ) % (ancho, alto, y(8), ancho, y(2) - y(8), HIELO_SUAVE,
         ancho, y(8), y(8), LINEA, ancho, y(2), y(2), LINEA, puntos, HIELO, fuera)


def tarjeta_sede(nombre, sede_id, actual, hoy, semana, serie):
    """Tarjeta del tablero para una sede."""
    if "error" in actual:
        return ('<div class="sede"><div class="sede-nombre">%s%s</div>'
                '<div class="sede-sub">Sin datos: %s</div></div>'
                % (icono("sede", 16), escape(nombre), escape(actual.get("mensaje", ""))))

    css = estado_css(actual["estado"])
    acento = {"ok": VERDE, "alta": ROJO, "baja": "#3B82F6"}[css]
    jornada = hoy.get("estado", "—") if "error" not in hoy else "—"
    episodios = semana.get("total_episodios", 0) if "error" not in semana else 0
    linea = "en línea" if actual["sensor_en_linea"] else "sin reportar"

    return (
        '<div class="sede" style="--acento:%s">'
        '<div class="sede-top"><div><div class="sede-nombre">%s%s</div>'
        '<div class="sede-id mono">%s</div></div>'
        '<span class="estado %s">%s</span></div>'
        '<div class="sede-cifra"><b>%.1f</b><span>°C</span></div>'
        '<div class="sede-sub">Lectura de las %s · hace %d min · sensor %s</div>'
        '%s'
        '<div class="sede-pie">'
        '<div>Jornada de hoy<strong>%s</strong></div>'
        '<div>Excursiones · 7 días<strong>%d</strong></div>'
        '</div></div>'
    ) % (acento, icono("sede", 16), escape(nombre), escape(sede_id), css,
         estado_texto(actual["estado"]), actual["lectura"],
         _hora(actual["registrada"]), actual["antiguedad_min"], linea,
         grafico(serie), escape(jornada.title() if jornada != "—" else jornada), episodios)


def seccion(texto, nombre_icono):
    return '<div class="seccion">%s%s</div>' % (icono(nombre_icono, 14), escape(texto))


_NOMBRES_ARG = {"sede": "Sede", "fecha": "Fecha", "fecha_inicio": "Desde", "fecha_fin": "Hasta",
                "desde": "Desde", "hasta": "Hasta", "tipo": "Tipo", "solo_alertas": "Solo alertas",
                "destinatario": "Para", "motivo": "Motivo"}


def _argumentos(args, sedes):
    if not args:
        return '<div class="args"><span class="arg">sin parámetros</span></div>'
    partes = []
    for k, v in args.items():
        valor = sedes.get(v, v) if k == "sede" else v
        valor = str(valor)
        if len(valor) > 48:
            valor = valor[:48] + "…"
        partes.append('<span class="arg"><b>%s</b>%s</span>' % (_NOMBRES_ARG.get(k, k), escape(valor)))
    return '<div class="args">%s</div>' % "".join(partes)


def _resultado(funcion, r, sedes):
    if "error" in r:
        return ('<div class="res error"><div class="res-err"><b>%s</b>%s</div></div>'
                % (escape(r["error"]), escape(r.get("mensaje", ""))))

    if funcion == "generar_resumen_jornada":
        ok = r["estado"] == "CONFORME"
        return (
            '<div class="res"><span class="veredicto %s">%s%s</span><div class="kpis">'
            '<div class="kpi"><span>Máxima</span><b>%s</b></div>'
            '<div class="kpi"><span>Mínima</span><b>%s</b></div>'
            '<div class="kpi"><span>Promedio</span><b>%.2f&nbsp;°C</b></div>'
            '<div class="kpi"><span>Cobertura</span><b>%.1f&nbsp;%%</b></div>'
            '<div class="kpi"><span>Lecturas</span><b>%d / %d</b></div>'
            '<div class="kpi"><span>Fuera de rango</span><b>%d</b></div>'
            '</div></div>'
        ) % ("ok" if ok else "no", escape(r["estado"]), " · parcial" if r["parcial"] else "",
             _t(r["maxima"]), _t(r["minima"]), r["promedio"], r["cobertura_pct"],
             r["total_lecturas"], r["lecturas_esperadas"], r["lecturas_fuera_de_rango"])

    if funcion == "consultar_excursiones_termicas":
        if not r["episodios"]:
            return '<div class="res"><span class="veredicto ok">Sin episodios en el periodo</span></div>'
        filas = "".join(
            '<tr><td class="%s">%s</td><td>%s %s–%s</td><td>%d min</td><td class="%s">%s</td><td>%d</td></tr>'
            % ("t-alta" if e["tipo"] == "ALERTA_ALTA" else "t-baja",
               "Alta" if e["tipo"] == "ALERTA_ALTA" else "Baja",
               _fecha_corta(e["inicio"]), _hora(e["inicio"]), _hora(e["fin"]),
               e["duracion_estimada_min"],
               "t-alta" if e["tipo"] == "ALERTA_ALTA" else "t-baja", _t(e["valor_extremo"]),
               e["lecturas_fuera_de_rango"])
            for e in r["episodios"])
        return ('<div class="res"><span class="veredicto no">%d episodio(s)</span>'
                '<table class="tabla"><tr><th>Tipo</th><th>Ventana</th><th>Dur.</th><th>Extremo</th><th>Lect.</th></tr>'
                '%s</table></div>') % (r["total_episodios"], filas)

    if funcion == "consultar_temperatura_actual":
        return (
            '<div class="res"><span class="veredicto %s">%s</span><div class="kpis">'
            '<div class="kpi"><span>Lectura</span><b>%s</b></div>'
            '<div class="kpi"><span>Hora</span><b>%s</b></div>'
            '<div class="kpi"><span>Antigüedad</span><b>%d min</b></div>'
            '</div></div>'
        ) % ("ok" if r["estado"] == "OK" else "no", estado_texto(r["estado"]),
             _t(r["lectura"]), _hora(r["registrada"]), r["antiguedad_min"])

    if funcion == "consultar_lecturas_periodo":
        filas = "".join(
            '<tr><td>%s</td><td class="%s">%s</td><td>%s</td></tr>'
            % (l["hora"], {"ALERTA_ALTA": "t-alta", "ALERTA_BAJA": "t-baja"}.get(l["estado"], ""),
               _t(l["t"]), estado_texto(l["estado"]))
            for l in r["lecturas"][:16])
        extra = "" if r["total"] <= 16 else '<div class="nodo-fn">y %d lecturas más</div>' % (r["total"] - 16)
        return ('<div class="res"><table class="tabla"><tr><th>Hora</th><th>Temp.</th><th>Estado</th></tr>'
                '%s</table>%s</div>') % (filas, extra)

    if funcion == "notificar_responsable":
        return (
            '<div class="res"><span class="veredicto ok">%s</span><div class="kpis">'
            '<div class="kpi"><span>Identificador</span><b class="mono" style="font-size:.78rem">%s</b></div>'
            '<div class="kpi"><span>Para</span><b style="font-size:.82rem">%s</b></div>'
            '<div class="kpi"><span>Canal</span><b style="font-size:.82rem">%s</b></div>'
            '</div></div>'
        ) % (escape(r["estado"].replace("_", " ")), escape(r["alerta_id"]),
             escape(r["destinatario"]), escape(r["canal"]))

    if funcion == "listar_sedes_autorizadas":
        chips = "".join('<span class="arg"><b>%s</b>%s</span>' % (escape(s["nombre"]), escape(s["id"]))
                        for s in r["sedes"]) or "Ninguna"
        return '<div class="res"><div class="args" style="margin:0">%s</div></div>' % chips

    return '<div class="res mono" style="font-size:.72rem">%s</div>' % escape(str(r))


def linea_de_tiempo(traza, huerfanas, sedes, desde_cache=False, pregunta=""):
    """El ciclo de herramientas del turno como linea de tiempo vertical."""
    if not traza:
        return ('<div class="evid"><div class="evid-vacio">Este turno se respondió con el contexto '
                'de la conversación, sin consultar datos nuevos.</div></div>')

    rondas = max(p["ronda"] for p in traza)
    total_ms = sum(p["ms"] for p in traza)
    meta = ('<div class="evid-meta"><span class="pill">%d llamada(s)</span>'
            '<span class="pill">%d ronda(s) de requires_action</span>'
            '<span class="pill">%d ms en herramientas</span>%s</div>'
            % (len(traza), rondas, total_ms,
               '<span class="pill">desde caché · sin costo</span>' if desde_cache else ""))

    nodos = []
    if pregunta:
        nodos.append('<div class="nodo"><div class="nodo-ico">%s</div>'
                     '<div class="nodo-tit">Pregunta del usuario</div>'
                     '<div class="nodo-fn">%s</div></div>' % (icono("pregunta", 13), escape(pregunta[:120])))

    for i, p in enumerate(traza, 1):
        error = "error" in p["resultado"]
        clase = "falla" if error else ("envio" if p["funcion"] == "notificar_responsable" else "")
        nodos.append(
            '<div class="nodo %s"><div class="nodo-ico">%s</div>'
            '<div class="nodo-tit">%s<small>ronda %d · %d ms</small></div>'
            '<div class="nodo-fn mono">%s</div>%s%s</div>'
            % (clase, icono("bloqueo" if error else ICONO_FUNCION.get(p["funcion"], "chip"), 13),
               escape(TITULO_FUNCION.get(p["funcion"], p["funcion"])), p["ronda"], p["ms"],
               escape(p["funcion"]), _argumentos(p["argumentos"], sedes),
               _resultado(p["funcion"], p["resultado"], sedes)))

    nodos.append('<div class="nodo fin"><div class="nodo-ico">%s</div>'
                 '<div class="nodo-tit">Respuesta redactada por el modelo</div>'
                 '<div class="nodo-fn">con los resultados anteriores como única fuente de cifras</div></div>'
                 % icono("verificado", 13))

    if huerfanas:
        sello = ('<div class="sello-fin no">%sCifras sin respaldo en las herramientas: %s</div>'
                 % (icono("alerta", 16), escape(", ".join(sorted(huerfanas)))))
    else:
        sello = ('<div class="sello-fin ok">%sVerificación de procedencia: todas las cifras provienen '
                 'de las herramientas</div>' % icono("verificado", 16))

    return '<div class="evid">%s<div class="tl">%s</div>%s</div>' % (meta, "".join(nodos), sello)


def pie(ruta_bitacora):
    return ('<div class="pie">Respuestas informativas. El acta de cumplimiento y la evaluación de los '
            'productos corresponden al químico farmacéutico responsable. Cada consulta queda registrada '
            'en <span class="mono">%s</span>.</div>' % escape(ruta_bitacora))
