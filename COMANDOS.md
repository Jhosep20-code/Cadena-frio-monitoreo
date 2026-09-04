# Guía de comandos — Sesión 03: Contenedorización

Ejecutar desde la raíz del proyecto, con Docker Desktop abierto.

---

## Parte A — Calentamiento con imágenes oficiales (5 min)

Cumple el requisito literal de la diapositiva.

```bash
# 1. La imagen de prueba más simple que existe
docker run hello-world

# 2. Levantar nginx oficial en segundo plano
docker run -d --name prueba-nginx -p 8081:80 nginx

# 3. Ver qué contenedores están corriendo
docker ps

# 4. Abrir http://localhost:8081 en el navegador

# 5. Detener y eliminar
docker stop prueba-nginx
docker rm prueba-nginx
```

---

## Parte B — Contenerizar nuestro proyecto (15 min)

```bash
# Construir la imagen a partir del Dockerfile
docker build -t cadena-frio:1.0 .

# Ver la imagen creada y su tamaño
docker images | grep cadena-frio

# Levantar un contenedor con la sede de Huancayo
docker run -d --name nodo-prueba -p 8000:8000 -e SEDE=almacen-huancayo cadena-frio:1.0

# Confirmar que está corriendo
docker ps

# Probar los tres endpoints
curl http://localhost:8000/health
curl "http://localhost:8000/clasificar?t=4.5"
curl "http://localhost:8000/clasificar?t=11.2"
curl -X POST http://localhost:8000/resumen -d '{"lecturas":[4.1,4.5,12.0,3.9]}'

# Ver los registros del contenedor
docker logs nodo-prueba

# Entrar al contenedor por dentro
docker exec -it nodo-prueba sh

# Detener
docker stop nodo-prueba
docker rm nodo-prueba
```

---

## Parte C — La demostración que impresiona (10 min)

Levanta dos sedes y un balanceador nginx con un solo comando.

```bash
# Levantar los tres contenedores
docker compose up -d --build

# Ver los tres corriendo
docker ps

# Consultar varias veces: el campo "sede" alterna entre almacenes
curl http://localhost:8080/health
curl http://localhost:8080/health
curl http://localhost:8080/health

# Ver los registros de todos los servicios
docker compose logs

# Apagar todo
docker compose down
```

**Lo que hay que señalar:** la misma imagen corre dos veces con configuración distinta. No duplicamos código, solo cambiamos una variable de entorno.

---

## Comandos de referencia

| Comando | Qué hace |
|---|---|
| `docker run` | Crea y arranca un contenedor a partir de una imagen |
| `docker ps` | Lista los contenedores en ejecución (`-a` incluye los detenidos) |
| `docker stop` | Detiene un contenedor en ejecución |
| `docker build` | Construye una imagen a partir del Dockerfile |
| `docker images` | Lista las imágenes descargadas o construidas |
| `docker logs` | Muestra la salida del contenedor |
| `docker exec -it` | Abre una sesión dentro del contenedor |
| `docker rm` / `docker rmi` | Elimina contenedores / imágenes |
| `docker compose up -d` | Levanta todos los servicios definidos |
| `docker compose down` | Detiene y elimina todo el conjunto |

---

## Si algo falla

- **"port is already allocated"** — el puerto está ocupado. Cambia el número de la izquierda: `-p 8001:8000`.
- **"Cannot connect to the Docker daemon"** — Docker Desktop no está abierto.
- **El build tarda mucho** — la primera vez descarga la imagen base de Python. Las siguientes usan caché.
- **No tienen Docker instalado** — usen Play with Docker (labs.play-with-docker.com), funciona desde el navegador.
