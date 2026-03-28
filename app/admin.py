"""
Módulo de administración para el bot de Telegram.
Maneja los comandos de gestión de usuarios (/admin).
"""
import re
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from acceso import es_admin, anadir_usuario, eliminar_usuario, listar_usuarios, registrar_comando_admin, buscar_nombre_por_id


def validar_user_id(user_id: str) -> bool:
    """Valida que un user_id tenga el formato correcto.
    
    Args:
        user_id: String con el user_id a validar.
    
    Returns:
        True si es válido, False en caso contrario.
    """
    if not user_id.isdigit():
        return False
    if len(user_id) < 7 or len(user_id) > 12:
        return False
    return True


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /admin y sus subcomandos.
    
    Formato:
        /admin add <user_id> <nombre> - Añadir usuario
        /admin remove <user_id> - Eliminar usuario
        /admin list - Listar usuarios
        /admin help - Mostrar ayuda
    
    Args:
        update: Update de Telegram.
        context: Contexto del handler.
    """
    user_id = str(update.effective_user.id)
    
    if not es_admin(user_id):
        await update.message.reply_text(
            "⛔ No tienes permiso para usar este comando.\n"
            "Solo el administrador puede ejecutar esta acción."
        )
        return
    
    if not context.args:
        await mostrar_ayuda(update)
        return
    
    comando = context.args[0].lower()
    
    if comando == "add":
        await cmd_add(update, context)
    elif comando == "remove":
        await cmd_remove(update, context)
    elif comando == "list":
        await cmd_list(update, context)
    elif comando == "help":
        await mostrar_ayuda(update)
    else:
        await update.message.reply_text(
            f"Comando desconocido: {comando}\n"
            "Usa /admin help para ver los comandos disponibles."
        )


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el subcomando /admin add.
    
    Uso: /admin add <user_id> <nombre>
    """
    admin_id = str(update.effective_user.id)
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Uso incorrecto.\n"
            "Correcto: /admin add <user_id> <nombre>\n"
            "Ejemplo: /admin add 123456789 Ignacio"
        )
        return
    
    user_id = context.args[1]
    nombre = " ".join(context.args[2:])
    
    if not validar_user_id(user_id):
        await update.message.reply_text(
            "❌ El user_id no parece válido.\n"
            "Debe ser un número de 7-12 dígitos."
        )
        return
    
    if not nombre or len(nombre.strip()) < 2:
        await update.message.reply_text(
            "❌ El nombre no puede estar vacío o ser muy corto.\n"
            "Mínimo 2 caracteres."
        )
        return
    
    exito, mensaje = anadir_usuario(user_id, nombre.strip())
    
    registrar_comando_admin(admin_id, "add", f"{user_id}|{nombre}", "OK" if exito else "FAIL")
    
    if exito:
        await update.message.reply_text(f"✅ {mensaje}")
    else:
        await update.message.reply_text(f"❌ {mensaje}")


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el subcomando /admin remove.
    
    Uso: /admin remove <user_id>
    """
    admin_id = str(update.effective_user.id)
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Uso incorrecto.\n"
            "Correcto: /admin remove <user_id>\n"
            "Ejemplo: /admin remove 123456789"
        )
        return
    
    user_id = context.args[1]
    
    if not validar_user_id(user_id):
        await update.message.reply_text(
            "❌ El user_id no parece válido.\n"
            "Debe ser un número de 7-12 dígitos."
        )
        return
    
    nombre = buscar_nombre_por_id(user_id)
    if nombre:
        user_display = f"{nombre} ({user_id})"
    else:
        user_display = user_id
    
    exito, mensaje = eliminar_usuario(user_id)
    
    registrar_comando_admin(admin_id, "remove", user_id, "OK" if exito else "FAIL")
    
    if exito:
        await update.message.reply_text(f"✅ {mensaje}")
    else:
        await update.message.reply_text(f"❌ {mensaje}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el subcomando /admin list.
    
    Lista todos los usuarios autorizados.
    """
    admin_id = str(update.effective_user.id)
    
    lista = listar_usuarios()
    
    registrar_comando_admin(admin_id, "list", None, "OK")
    
    await update.message.reply_text(f"📋 {lista}")


async def mostrar_ayuda(update: Update) -> None:
    """Muestra la ayuda de comandos de administrador."""
    admin_id = str(update.effective_user.id)
    
    texto = (
        "🔧 *Comandos de Administrador*\n\n"
        "*Añadir usuario:*\n"
        "`/admin add <user_id> <nombre>`\n"
        "Ejemplo: `/admin add 123456789 Ignacio`\n\n"
        "*Eliminar usuario:*\n"
        "`/admin remove <user_id>`\n"
        "Ejemplo: `/admin remove 123456789`\n\n"
        "*Listar usuarios:*\n"
        "`/admin list`\n\n"
        "*Esta ayuda:*\n"
        "`/admin help`"
    )
    
    registrar_comando_admin(admin_id, "help", None, "OK")
    
    await update.message.reply_text(texto, parse_mode="Markdown")
