# Pipeline CI/CD — Monitoreo de cadena de frío

Experiencia Grupal · Sesión 02 · Unidad 1: DevOps y automatización de procesos
Herramientas de Desarrollo Profesional – TIC (10000096SI) · UTP Huancayo

## Integrantes

- Guillermo Laura, Maycol
- Paredes Amaya, Alexandro
- Tomas Silvestre, Niels
- Yachi García, Jhosep
- García Ramón, Jesús
- Paredes Quispe, Lindbergh

## Caso

Validación de lecturas de temperatura para el almacenamiento de medicamentos
termolábiles, que deben conservarse entre 2 °C y 8 °C. El módulo clasifica cada
lectura, detecta excursiones térmicas y genera el resumen diario que alimenta el
acta de cumplimiento.

## Etapas del pipeline

| Etapa | Job | Qué hace |
|---|---|---|
| Compilación | `build` | Instala dependencias, verifica que el módulo compila y publica el artefacto etiquetado con el SHA del commit. |
| Pruebas | `test` | Ejecuta 14 pruebas unitarias con pytest y exige una cobertura mínima del 80 %. |
| Despliegue simulado | `deploy` | Copia el artefacto a la carpeta `staging/`, ejecuta una verificación posterior e imprime la confirmación. |

Los jobs se encadenan con `needs`, de modo que si las pruebas fallan el
despliegue nunca llega a ejecutarse.

## Quality gate

El parámetro `--cov-fail-under=80` detiene el pipeline cuando la cobertura cae
por debajo del umbral acordado. La cobertura actual es del 91 %.

## Ejecución local

```bash
pip install -r requirements.txt
pytest --cov=src --cov-report=term-missing
python -m src.monitor
```

## Estructura

```
proyecto/
├── src/
│   └── monitor.py
├── tests/
│   └── test_monitor.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
└── README.md
```
