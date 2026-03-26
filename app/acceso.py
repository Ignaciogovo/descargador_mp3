"""
Módulo de control de acceso para el bot de Telegram.
Gestiona usuarios autorizados y registro de intentos no autorizados.
"""
import os
import logging
import functools
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Union
from logging.handlers import TimedRotatingFileHandler


CARPETA_CONFIG = "/app/config"
CARPETA_LOGS = "/app/logs"
ARCHIVO_USUARIOS = os.path.join(CARPETA_CONFIG, "usuarios_autorizados.txt")
ARCHIVO_LOG = os.path.join(CARPETA_LOGS, "access.log")

_logger = None


def _obtener_logger() -> logging.Logger:
    """Obtiene o crea el logger de acceso."""
    global _logger
    if _logger is not None:
        return _logger
    
    _crear_carpeta_logs()
    
    _logger = logging.getLogger("access_control")
    _logger.setLevel(logging.INFO)
    
    if not _logger.handlers:
        handler = TimedRotatingFileHandler(
            ARCHIVO_LOG,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        handler.setLevel(logging.INFO)
        
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formato)
        _logger.addHandler(handler)
    
    return _logger


def _crear_carpeta_logs() -> None:
    """Crea la carpeta de logs si no existe."""
    try:
        Path(CARPETA_LOGS).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"[ACCESO] Error creando carpeta logs: {e}")


def _crear_archivo_usuarios_si_no_existe() -> None:
    """Crea el archivo de usuarios autorizados si no existe."""
    if not os.path.exists(ARCHIVO_USUARIOS):
        try:
            Path(CARPETA_CONFIG).mkdir(parents=True, exist_ok=True)
            Path(ARCHIVO_USUARIOS).touch()
        except OSError as e:
            print(f"[ACCESO] Error creando archivo usuarios: {e}")


@functools.lru_cache(maxsize=1)
def obtener_usuarios_autorizados() -> set:
    """Obtiene la lista de usuarios autorizados desde el archivo.
    
    Usa lru_cache para cachear el resultado. Se limpia el cache
    cuando se modifica el archivo de usuarios.
    
    Returns:
        Set de user_ids autorizados como strings.
    """
    _crear_archivo_usuarios_si_no_existe()
    
    usuarios = set()
    try:
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    usuarios.add(linea.strip())
    except FileNotFoundError:
        pass
    except IOError as e:
        print(f"[ACCESO] Error leyendo usuarios: {e}")
    
    return usuarios


def limpiar_cache_usuarios() -> None:
    """Limpia el cache de usuarios para forzar re-lectura."""
    obtener_usuarios_autorizados.cache_clear()


def es_usuario_autorizado(user_id: Union[int, str]) -> bool:
    """Verifica si un usuario está autorizado.
    
    Args:
        user_id: ID del usuario de Telegram.
    
    Returns:
        True si el usuario está autorizado, False en caso contrario.
    """
    user_id_str = str(user_id)
    usuarios = obtener_usuarios_autorizados()
    return user_id_str in usuarios


def registrar_intento_bloqueado(user_id: Union[int, str], comando: Optional[str] = None, chat_id: Optional[int] = None) -> None:
    """Registra un intento de acceso no autorizado.
    
    Args:
        user_id: ID del usuario que intentó acceder.
        comando: Comando o mensaje que intentó ejecutar.
        chat_id: ID del chat donde ocurrió el intento.
    """
    logger = _obtener_logger()
    
    partes = [f"user_id={user_id}"]
    if comando:
        partes.append(f"comando={comando}")
    if chat_id:
        partes.append(f"chat_id={chat_id}")
    
    mensaje = " | ".join(partes)
    logger.warning(mensaje)


def registrar_acceso_permitido(user_id: Union[int, str], comando: Optional[str] = None) -> None:
    """Registra un acceso permitido (para auditoria).
    
    Args:
        user_id: ID del usuario que accedió.
        comando: Comando que ejecutó.
    """
    logger = _obtener_logger()
    
    partes = [f"user_id={user_id}", "ACCESS=OK"]
    if comando:
        partes.append(f"comando={comando}")
    
    mensaje = " | ".join(partes)
    logger.info(mensaje)


def requiere_autorizacion(func: Callable) -> Callable:
    """Decorador para requerir autorización en un handler de Telegram.
    
    Uso:
        @requiere_autorizacion
        async def mi_comando(update, context):
            ...
    """
    @functools.wraps(func)
    async def wrapper(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        user_id = update.effective_user.id
        
        if hasattr(update, "message"):
            comando = update.message.text
        elif hasattr(update, "callback_query"):
            comando = update.callback_query.data
        else:
            comando = None
        
        chat_id = update.effective_chat.id if hasattr(update, "effective_chat") else None
        
        if not es_usuario_autorizado(user_id):
            registrar_intento_bloqueado(user_id, comando, chat_id)
            
            if hasattr(update, "message"):
                await update.message.reply_text(
                    "⛔ No tienes permiso para usar este bot.\n"
                    "Contacta con el administrador si crees que esto es un error."
                )
            elif hasattr(update, "callback_query"):
                await update.callback_query.answer()
                await update.callback_query.message.reply_text(
                    "⛔ No tienes permiso para usar este bot.\n"
                    "Contacta con el administrador si crees que esto es un error."
                )
            return False
        
        registrar_acceso_permitido(user_id, comando)
        return await func(update, context)
    
    return wrapper


def agregar_usuario(user_id: str) -> bool:
    """Añade un usuario a la lista de autorizados.
    
    Args:
        user_id: ID del usuario a añadir.
    
    Returns:
        True si se añadió correctamente.
    """
    _crear_archivo_usuarios_si_no_existe()
    
    try:
        with open(ARCHIVO_USUARIOS, "a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")
        limpiar_cache_usuarios()
        return True
    except IOError as e:
        print(f"[ACCESO] Error añadiendo usuario: {e}")
        return False


def obtener_ruta_config() -> str:
    """Retorna la ruta del archivo de configuración de usuarios."""
    return ARCHIVO_USUARIOS


def obtener_ruta_log() -> str:
    """Retorna la ruta del archivo de log de acceso."""
    return ARCHIVO_LOG
