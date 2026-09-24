# Termo — Asistente de consulta del histórico térmico

Implementación funcional del diseño de la **TA2**, sobre el mismo proyecto de la TA1.
Unidad 2 · Herramientas de Desarrollo Profesional – TIC · UTP Huancayo

## Encaje con la hoja de ruta del proyecto

| Lo que pide la guía interna | Cómo se cumple |
|---|---|
| Asistente sobre Streamlit que consulta el histórico en lenguaje natural | `asistente/app.py` + las 6 herramientas sobre `monitor.py` |
| ...y **envía alertas** | `notificar_responsable` + `alertas.py` (webhook o bitácora) |
| Demostración en vivo con 3 preguntas y el prompt documentado | Guion de abajo; el prompt se ve en la barra lateral y está en `prompt_sistema.txt` |
| Regla de oro: desplegable por el pipeline | `Dockerfile.asistente`, `compose.asistente.yml` y `ci.asistente.yml` |
| Gate 1: cobertura ≥ 80 %, cero pruebas fallidas | 51 pruebas, 93 % sobre `asistente/` |
| Gate 2: sin credenciales ni vulnerabilidades | Clave por variable de entorno; Gitleaks y Trivy en el job |
| Riesgo de costos de API | Caché local de respuestas + tres proveedores, dos con capa gratuita |

## Qué hace

Responde en lenguaje natural preguntas sobre las cámaras de frío (`almacen-huancayo`
y `almacen-jauja`) apoyándose en cinco funciones que ejecutan el `monitor.py` de la
TA1. El modelo **redacta**; las cifras **siempre** salen del código.

La interfaz muestra, debajo de cada respuesta, el ciclo completo: qué función pidió
el modelo, con qué argumentos, qué devolvió el sistema y cuánto tardó. Ese panel es
la versión visible del estado `requires_action` que describe el documento.

## Archivos para integrar al proyecto

Estos tres no se copian tal cual: su contenido se agrega a los archivos que ya existen.

- `compose.asistente.yml` → pegar el bloque dentro de `services:` en `docker-compose.yml`
- `ci.asistente.yml` → pegar el job en `.github/workflows/ci.yml`, y cambiar `deploy: needs: test` por `needs: [test, asistente]`
- `.coveragerc.asistente` → reemplaza el `.coveragerc` actual

`Dockerfile.asistente` y `requirements_asistente.txt` sí van tal cual en la raíz.
La carpeta `.streamlit/` también va en la raíz: lleva el tema de color de la app.

## Diseño de la interfaz

La pantalla funciona como un centro de control, no como un chat suelto:

- **Cabecera**: marca, estado del monitor y proveedor y modelo en uso.
- **Tablero de cámaras**: una tarjeta por sede con la temperatura actual, su estado,
  el gráfico de las lecturas de hoy con la banda de 2 a 8 °C sombreada, el estado de la
  jornada y las excursiones de la semana. Se calcula con las mismas herramientas, sin
  llamar al modelo, así que no consume cuota.
- **Conversación** a la izquierda.
- **Evidencia del turno** a la derecha: el ciclo `requires_action` como línea de tiempo.
  Cada nodo muestra qué pidió el modelo (etiquetas), qué devolvió el monitor
  (indicadores y tablas) y cuánto tardó. Cierra con la verificación de procedencia.
  El JSON técnico sigue disponible en *Ver contrato JSON de cada llamada*.

Sin emojis: iconos de línea en SVG y símbolos Material. En celular, la barra lateral
se pliega y los bloques se apilan. La presentación vive en `ui.py` y se prueba como
el resto del código; `app.py` solo decide la disposición.

## Instalación (Windows, desde la carpeta `proy`)

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### Proveedor de IA

Los tres usan la misma biblioteca `openai` y el mismo ciclo de llamada a funciones;
solo cambian la dirección del servidor y el nombre del modelo.

| Proveedor | Clave | Modelo por defecto | Costo |
|---|---|---|---|
| Google Gemini | `GEMINI_API_KEY` (aistudio.google.com/apikey) | `gemini-3.6-flash` | gratis |
| Groq | `GROQ_API_KEY` (console.groq.com/keys) | `llama-3.3-70b-versatile` | gratis |
| OpenAI | `OPENAI_API_KEY` (platform.openai.com) | `gpt-4o-mini` | requiere saldo |

Pega la clave en la barra lateral, o expórtala antes de arrancar:

```powershell
$env:GEMINI_API_KEY = "tu_clave"
streamlit run asistente/app.py
```

**Si aparece un error de modelo inexistente**, pulsa *Consultar modelos disponibles*
en la barra lateral y pega en el campo *Modelo* el nombre vigente. Google y Groq
retiran versiones cada pocas semanas; por eso el campo es editable y no está fijo
en el código.

Se abre en http://localhost:8501.

## Pruebas

```powershell
pytest tests_asistente --cov=asistente --cov-fail-under=80 -v
```

51 pruebas, sin red y sin consumir la API: un cliente falso simula que el modelo
pide funciones, y así se verifica el ciclo completo.

## Estructura

```
asistente/
├── app.py                 interfaz Streamlit + panel del ciclo de herramientas
├── agente.py              ciclo pedir función → ejecutar → devolver resultado
├── herramientas.py        las 5 funciones, validación de acceso y bitácora
├── herramientas.json      esquemas JSON Schema que ve el modelo
├── repositorio.py         lecturas simuladas, deterministas por sede y fecha
├── alertas.py             canal de alertas: webhook o bitácora local
├── verificacion.py        M1: ninguna cifra sin respaldo
├── ui.py                  estilos, iconos, tablero y línea de tiempo
├── logo.svg               identidad visual (escudo, copo, termómetro)
└── prompt_sistema.txt     el prompt de la sección 3 del documento
```

`src/monitor.py` no se modificó: las herramientas lo importan tal cual.

## Datos de la demostración

Son deterministas, así que la demo sale igual todas las veces:

| Sede | Día | Qué ocurrió |
|---|---|---|
| Jauja | ayer | Excursión alta de 03:15 a 04:00, pico de 9.6 °C, 4 lecturas fuera de rango y 2 lecturas perdidas (cobertura 97.9 %). **NO CONFORME** |
| Huancayo | ayer | Sin incidentes. **CONFORME** |
| Huancayo | hace 4 días | Excursión baja de 23:00 a 23:30, mínima de 1.4 °C |

## Guion sugerido para la exposición

1. **"¿Cómo le fue a Jauja ayer? ¿Hubo algún problema?"**
   Abre el panel: el modelo pidió dos funciones en paralelo. Muestra que la
   respuesta dice *1 episodio con 4 lecturas fuera de rango*, no "4 excursiones".
2. **"¿Y Huancayo?"**
   Sin repetir fecha ni tema: demuestra la memoria de la conversación.
3. **"Avísale al químico farmacéutico de turno sobre esa excursión."**
   Confirma el destinatario, envía la alerta y devuelve su identificador y estado.
   Si no hay webhook, queda en `bitacora/alertas.jsonl`. Prueba también pedir una
   alerta sobre Huancayo de ayer: responde `SIN_EXCURSION` y no envía nada.
4. **Quita `almacen-jauja` de las sedes autorizadas y vuelve a preguntar por Jauja.**
   La función devuelve `ACCESO_DENEGADO` y no entrega ningún dato. La autorización
   se decide en el código, no en el prompt.
5. **"¿Puedo seguir usando las vacunas que estuvieron en esa cámara?"**
   Entrega los datos del episodio y deriva la decisión al químico farmacéutico.
6. **"¿Qué temperatura hubo el mes que viene?"**
   Responde que la fecha aún no ha ocurrido, sin llamar a ninguna herramienta.
7. Cierra mostrando el aviso verde de **verificación de procedencia** y la
   bitácora `bitacora/auditoria.jsonl`, que registra cada llamada.

## Diferencia con el documento

El documento diseña sobre la **API de Asistentes**, que OpenAI retiró el 26 de
agosto de 2026. Esta implementación usa el mismo ciclo sobre Chat Completions con
llamada a funciones —la alternativa A de la tabla comparativa— porque funciona hoy
y es gratuita con Groq. Lo único que cambia es quién guarda el historial: aquí lo
guarda la aplicación (`st.session_state`) en vez del servidor (`Thread`). El prompt,
las cinco herramientas, `tools.py` y `monitor.py` son idénticos.

Groq no admite el modo `strict` de los esquemas, así que `agente.py` lo retira
automáticamente según el proveedor.
