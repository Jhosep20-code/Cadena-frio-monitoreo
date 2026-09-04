# Imagen oficial de Python, variante slim para reducir el tamano final
FROM python:3.12-slim

# Metadatos del proyecto
LABEL proyecto="monitor-cadena-frio"
LABEL curso="Herramientas de Desarrollo Profesional - TIC"

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero las dependencias para aprovechar la cache de capas:
# si el codigo cambia pero requirements.txt no, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ahora si copiamos el codigo fuente
COPY src/ ./src/

# Usuario sin privilegios: buena practica de seguridad,
# evita que el proceso corra como root dentro del contenedor
RUN useradd --create-home monitor
USER monitor

# Variables de entorno configurables al levantar el contenedor
ENV PUERTO=8000
ENV SEDE=sede-principal

# Puerto que el contenedor expone
EXPOSE 8000

# Verificacion de salud: Docker consulta este endpoint periodicamente
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando que se ejecuta al arrancar
CMD ["python", "-m", "src.api"]
