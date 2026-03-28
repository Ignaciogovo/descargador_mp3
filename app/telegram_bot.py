import os
import re
import asyncio
from typing import Optional
import nest_asyncio
nest_asyncio.apply()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from gestion_download import download_mp3
from cola_descargas import cola_descargas
from acceso import requiere_autorizacion, es_usuario_autorizado, registrar_intento_bloqueado, es_admin, buscar_nombre_por_id
from admin import admin_command
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

print(f"[TELEGRAM_BOT] Token encontrado: {'SI' if TOKEN else 'NO'}")
if TOKEN:
    print(f"[TELEGRAM_BOT] Token (primeros 5 chars): {TOKEN[:5]}...")
else:
    print("[TELEGRAM_BOT] DEBUG - Todas las vars de entorno:", dict(os.environ))

URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/playlist\?list=)'
    r'[\w\-]+(?:&[\w=&-]*)?|'
    r'https?://(?:www\.)?[\w\-]+\.[\w\-]+(?:/[\w\-./?=&#%]*)?',
    re.IGNORECASE
)

YOUTUBE_VIDEO_PATTERN = re.compile(r'(?:v=|/)([a-zA-Z0-9_-]{11})')

def extraer_video_id(url: str) -> Optional[str]:
    match = YOUTUBE_VIDEO_PATTERN.search(url)
    if match:
        return match.group(1)
    return None

def normalizar_url(url: str) -> str:
    video_id = extraer_video_id(url)
    if video_id:
        return f"https://youtu.be/{video_id}"
    return url

user_sessions = {}
url_cache = {}  # {f"{user_id}|{video_id}": url_original}

def crear_callback_telegram(user_id, chat_id, context, formato=None):
    """Crea un callback para manejar los estados de la descarga"""
    def callback_telegram_sync(estado, **kwargs):
        posicion = kwargs.get('posicion', 0)
        archivo = kwargs.get('archivo', '')
        
        async def enviar_mensaje_async():
            if estado == "en_cola":
                mensaje = (
                    f"⏳ Tu descarga está en cola.\n"
                    f"📍 Posición: {posicion + 1}\n"
                    f"Te notificaré cuando cambie la posición y cuando termine."
                )
                await context.bot.send_message(chat_id=chat_id, text=mensaje)
            
            elif estado == "avance_cola":
                mensaje = f"📍 Tu descarga ha avanzado. Nueva posición: {posicion + 1}"
                await context.bot.send_message(chat_id=chat_id, text=mensaje)
            
            elif estado == "descargando":
                mensaje = "🔄 Tu descarga está siendo procesada..."
                await context.bot.send_message(chat_id=chat_id, text=mensaje)
            
            elif estado == "completado":
                if archivo and not archivo.startswith("Error:"):
                    with open(archivo, "rb") as f:
                        if formato and formato.lower() == "mp3":
                            await context.bot.send_audio(chat_id=chat_id, audio=f)
                        else:
                            await context.bot.send_video(chat_id=chat_id, video=f)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ ¡Descarga completada! 🎵\nFormato: {formato.upper() if formato else 'MP3'}"
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ Error en la descarga:\n{archivo or 'Error desconocido'}"
                    )
        
        try:
            asyncio.run(enviar_mensaje_async())
        except Exception as e:
            print(f"[TELEGRAM] Error en callback {estado}: {e}")
    
    return callback_telegram_sync


@requiere_autorizacion
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! 🎵\n\n"
        "Soy el bot de descarga de música/videos.\n"
        "Envíame una URL de YouTube y te preguntaré si quieres descargar MP3 o MP4."
    )


@requiere_autorizacion
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/start - Iniciar el bot\n"
        "/help - Ver ayuda\n\n"
        "Solo envíame una URL de YouTube y selecciona el formato."
    )


def es_url_valida(texto: str) -> bool:
    return bool(URL_PATTERN.match(texto.strip()))


@requiere_autorizacion
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.strip()

    if not es_url_valida(texto):
        await update.message.reply_text(
            "⚠️ La URL no parece válida. Por favor, envíame una URL de YouTube."
        )
        return

    video_id = extraer_video_id(texto)
    if video_id:
        cache_key = f"{user_id}|{video_id}"
        url_cache[cache_key] = texto

    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3", callback_data=f"mp3|{video_id}"),
            InlineKeyboardButton("🎬 MP4", callback_data=f"mp4|{video_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"¿Qué formato deseas descargar?\n\n"
        f"URL: {texto}",
        reply_markup=reply_markup
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from acceso import es_usuario_autorizado, registrar_intento_bloqueado, registrar_acceso_permitido
    
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    
    if not es_usuario_autorizado(user_id):
        registrar_intento_bloqueado(user_id, query.data)
        await query.message.reply_text(
            "⛔ No tienes permiso para usar este bot.\n"
            "Contacta con el administrador si crees que esto es un error."
        )
        return
    
    registrar_acceso_permitido(user_id, query.data)
    
    user_id_str = str(query.from_user.id)
    data = query.data
    chat_id = query.message.chat_id

    formato, video_id = data.split("|", 1)

    await query.edit_message_reply_markup(reply_markup=None)

    cache_key = f"{user_id}|{video_id}"
    url = url_cache.pop(cache_key, f"https://youtu.be/{video_id}")

    callback_estado = crear_callback_telegram(user_id, chat_id, context, formato)
    exito, posicion = cola_descargas.agregar(user_id, url, formato, estado_callback=callback_estado)
    
    if not exito:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ {posicion}")
        return
    
    if posicion == 0:
        mensaje = "🔄 Tu descarga está siendo procesada..."
    else:
        mensaje = f"⏳ Tu descarga está en cola.\n📍 Posición: {posicion + 1}\nTe notificaré cuando avance o termine."
    
    await context.bot.send_message(chat_id=chat_id, text=mensaje)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error en el bot: {context.error}")


async def main():
    if not TOKEN:
        print("[TELEGRAM_BOT] ERROR: TELEGRAM_BOT_TOKEN no configurado")
        return

    print("[TELEGRAM_BOT] Creando Application...")
    app = Application.builder().token(TOKEN).build()
    print("[TELEGRAM_BOT] Application creada")

    print("[TELEGRAM_BOT] Añadiendo handlers...")
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    print("[TELEGRAM_BOT] Handlers añadidos")

    print(f"[TELEGRAM_BOT] Iniciando polling (token: {TOKEN[:10]}...)")
    
    async with app:
        print("[TELEGRAM_BOT] Ejecutando run_polling...")
        await app.run_polling(drop_pending_updates=True)
        print("[TELEGRAM_BOT] Polling iniciado correctamente")


async def iniciar_bot():
    print("[TELEGRAM_BOT] Iniciando bot...")
    if not TOKEN:
        print("[TELEGRAM_BOT] ERROR: TELEGRAM_BOT_TOKEN no configurado")
        return

    print("[TELEGRAM_BOT] Ejecutando main()...")
    try:
        await main()
    except KeyboardInterrupt:
        print("[TELEGRAM_BOT] Interrumpido por usuario")
    except Exception as e:
        print(f"[TELEGRAM_BOT] Error general: {e}")


if __name__ == "__main__":
    asyncio.run(iniciar_bot())
