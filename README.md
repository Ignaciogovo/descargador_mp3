# Descargador MP3/MP4

Este programa te permite descargar videos de YouTube en formato MP3 y MP4 desde tu propio entorno, evitando la publicidad abusiva y riesgos de seguridad que puedan tener los convertidores que se encuentran en internet. Este proyecto nació al no saber responder a un conocido si esos convertidores en internet son seguros, y aunque hoy en día no se usen mucho, si es que es mejor tenerlo para evitar cualquier problema de seguridad.

Está desarrollado en **Python** y empaquetado con **Docker** para una instalación sencilla.

---

## Funcionalidades

- ✅ Descarga de vídeos de YouTube en formato **MP3** y **MP4**
- ✅ **Bot de Telegram** para descargas desde el móvil
- ✅ **Sistema de colas** con notificaciones de progreso
- ✅ **Cover art** automático (thumbnail del vídeo como imagen del álbum)
- ✅ **Control de acceso** para el bot de Telegram (solo usuarios autorizados)
- ✅ **Limpieza automática** de archivos después de 2 horas
- ✅ **Logs de acceso** con retención de 7 días

---

## Requisitos

- Docker y Docker Compose instalados
- Token de bot de Telegram (opcional, solo si usas el bot)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Ignaciogovo/descargador_mp3.git
cd descargador_mp3/app
```

### 2. Configurar variables de entorno

```bash
cp config/.env.example .env
```

Edita el archivo `.env` y añade tu token de Telegram:

```
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### 3. Configurar usuarios autorizados (Telegram)

Edita el archivo `config/usuarios_autorizados.txt` y añade tu ID de Telegram (un usuario por línea):

```
123456789
987654321
```

Para obtener tu ID de Telegram, talk to [@userinfobot](https://t.me/userinfobot) in Telegram.

### 4. Construir y ejecutar

```bash
docker-compose up -d
```

---

## Uso

### Web

Accede a http://127.0.0.1:5000 desde tu navegador:

1. Introduce una URL de YouTube
2. Selecciona el formato (MP3 o MP4)
3. Pulsa "Procesar"
4. Espera a que termine la descarga
5. Pulsa el botón de descarga

### Telegram

1. Busca tu bot en Telegram
2. Envía `/start`
3. Envía una URL de YouTube
4. Selecciona MP3 o MP4
5. Recibe el archivo cuando termine

---

## Configuración

### Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | (requerido) |
| `MODO` | Modo de ejecución: `web`, `telegram` o `ambos` | `ambos` |
| `MAX_COLA_DESCARGAS` | Máximo de descargas simultáneas | `50` |

### Modo de ejecución

Puedes ejecutar solo la web, solo Telegram, o ambos:

```bash
# Solo web
MODO=web docker-compose up -d

# Solo Telegram
MODO=telegram docker-compose up -d

# Ambos (default)
MODO=ambos docker-compose up -d
```

---

## Logs

Los archivos de log se encuentran en la carpeta `/logs` dentro del contenedor:

| Archivo | Descripción |
|---------|-------------|
| `access.log` | Intentos de acceso al bot (usuarios autorizados y bloqueados) |
| `cola_descargas.log` | Actividad del sistema de colas |

Los logs se mantienen automáticamente durante 7 días.

---

## Mantenimiento

### Añadir usuarios autorizados

Puedes usar el script incluido:

```bash
./agregar_usuario.sh 123456789
```

O editar directamente `config/usuarios_autorizados.txt`.

### Ver logs en tiempo real

```bash
docker-compose logs -f
```

---

## ⚠️ Notas importantes

- Este proyecto es para fines educativos. Evita usarlo para actividades fraudulentas o ilegales.
- Los archivos se borran automáticamente después de 2 horas.
- Solo los usuarios listados en `usuarios_autorizados.txt` pueden usar el bot de Telegram.
- Asegúrate de tener Docker y Docker Compose instalados.

---

## Tecnologías

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Descarga de vídeos
- [FFmpeg](https://ffmpeg.org/) - Procesamiento de audio/vídeo
- [Flask](https://flask.palletsprojects.com/) - Interfaz web
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Bot de Telegram
- [Docker](https://www.docker.com/) - Contenedor

---

## Imagen de la aplicación

![Imagen de la web](https://github.com/Ignaciogovo/descargador_mp3/blob/master/varios/imagenes/index.png)
