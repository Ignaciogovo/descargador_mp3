"""
Módulo de control de acceso para el bot de Telegram.
Gestiona usuarios autorizados y registro de intentos no autorizados.
"""
import os
import logging
import functools
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Union, Dict, Tuple
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
def _obtener_usuarios_raw() -> Dict[str, str]:
    """Obtiene diccionario de usuarios {user_id: nombre} desde el archivo.
    
    Usa lru_cache para cachear el resultado.
    
    Returns:
        Dict de {user_id: nombre}.
    """
    _crear_archivo_usuarios_si_no_existe()
    
    usuarios = {}
    try:
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    partes = linea.split("|")
                    if len(partes) >= 2:
                        user_id = partes[0].strip()
                        nombre = partes[1].strip()
                        usuarios[user_id] = nombre
                    elif len(partes) == 1 and partes[0].strip():
                        usuarios[partes[0].strip()] = "Sin nombre"
    except FileNotFoundError:
        pass
    except IOError as e:
        print(f"[ACCESO] Error leyendo usuarios: {e}")
    
    return usuarios


def obtener_usuarios_autorizados() -> set:
    """Obtiene la lista de user_ids autorizados.
    
    Returns:
        Set de user_ids autorizados como strings.
    """
    return set(_obtener_usuarios_raw().keys())


def limpiar_cache_usuarios() -> None:
    """Limpia el cache de usuarios para forzar re-lectura."""
    _obtener_usuarios_raw.cache_clear()


def es_admin(user_id: Union[int, str]) -> bool:
    """Verifica si un usuario es el administrador.
    
    Args:
        user_id: ID del usuario de Telegram.
    
    Returns:
        True si es el administrador, False en caso contrario.
    """
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID')
    if not admin_id:
        print("[ACCESO] ADVERTENCIA: TELEGRAM_ADMIN_ID no está configurado")
        return False
    return str(user_id) == admin_id


def es_usuario_autorizado(user_id: Union[int, str]) -> bool:
    """Verifica si un usuario está autorizado o es admin.
    
    Args:
        user_id: ID del usuario de Telegram.
    
    Returns:
        True si el usuario está autorizado o es admin, False en caso contrario.
    """
    user_id_str = str(user_id)
    if es_admin(user_id_str):
        return True
    return user_id_str in obtener_usuarios_autorizados()


def buscar_nombre_por_id(user_id: Union[int, str]) -> Optional[str]:
    """Busca el nombre de un usuario por su ID.
    
    Args:
        user_id: ID del usuario.
    
    Returns:
        Nombre del usuario o None si no existe.
    """
    user_id_str = str(user_id)
    usuarios = _obtener_usuarios_raw()
    return usuarios.get(user_id_str)


def registrar_intento_bloqueado(user_id: Union[int, str], comando: Optional[str] = None, chat_id: Optional[int] = None) -> None:
    """Registra un intento de acceso no autorizado.
    
    Args:
        user_id: ID del usuario que intentó acceder.
        comando: Comando o mensaje que intentó ejecutar.
        chat_id: ID del chat donde ocurrió el intento.
    """
    logger = _obtener_logger()
    
    nombre = buscar_nombre_por_id(user_id)
    user_display = f"{nombre} ({user_id})" if nombre else str(user_id)
    
    partes = [f"user_id={user_id}", f"nombre={nombre or 'desconocido'}"]
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


def anadir_usuario(user_id: str, nombre: str) -> Tuple[bool, str]:
    """Añade un usuario a la lista de autorizados.
    
    Args:
        user_id: ID del usuario a añadir.
        nombre: Nombre del usuario.
    
    Returns:
        Tuple (éxito, mensaje).
    """
    if not user_id.isdigit():
        return False, "El user_id debe ser numérico"
    
    if len(user_id) < 7 or len(user_id) > 12:
        return False, "El user_id no parece válido"
    
    if not nombre or len(nombre.strip()) == 0:
        return False, "El nombre no puede estar vacío"
    
    nombre_limpio = nombre.strip().replace('\n', '').replace('\r', '').replace('\t', '')
    
    if len(nombre_limpio) < 2:
        return False, "El nombre es demasiado corto"
    
    if len(nombre_limpio) > 50:
        return False, "El nombre es demasiado largo (máx 50 caracteres)"
    
    _crear_archivo_usuarios_si_no_existe()
    
    usuarios = _obtener_usuarios_raw()
    if user_id in usuarios:
        return False, f"El usuario {user_id} ya está autorizado como '{usuarios[user_id]}'"
    
    try:
        with open(ARCHIVO_USUARIOS, "a", encoding="utf-8") as f:
            f.write(f"{user_id}|{nombre_limpio}\n")
        limpiar_cache_usuarios()
        return True, f"Usuario '{nombre_limpio}' ({user_id}) añadido correctamente"
    except IOError as e:
        print(f"[ACCESO] Error añadiendo usuario: {e}")
        return False, "Error al escribir en el archivo"


def eliminar_usuario(user_id: str) -> Tuple[bool, str]:
    """Elimina un usuario de la lista de autorizados.
    
    Args:
        user_id: ID del usuario a eliminar.
    
    Returns:
        Tuple (éxito, mensaje).
    """
    if not user_id.isdigit():
        return False, "El user_id debe ser numérico"
    
    usuarios = _obtener_usuarios_raw()
    if user_id not in usuarios:
        return False, f"El usuario {user_id} no está en la lista"
    
    nombre = usuarios[user_id]
    
    try:
        with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
            for uid, nom in usuarios.items():
                if uid != user_id:
                    f.write(f"{uid}|{nom}\n")
        limpiar_cache_usuarios()
        return True, f"Usuario '{nombre}' ({user_id}) eliminado correctamente"
    except IOError as e:
        print(f"[ACCESO] Error eliminando usuario: {e}")
        return False, "Error al escribir en el archivo"


def listar_usuarios() -> str:
    """Lista todos los usuarios autorizados.
    
    Returns:
        String formateado con la lista de usuarios.
    """
    usuarios = _obtener_usuarios_raw()
    
    if not usuarios:
        return "No hay usuarios autorizados"
    
    lineas = ["Usuarios autorizados:"]
    for i, (uid, nom) in enumerate(usuarios.items(), 1):
        lineas.append(f"{i}. {nom} ({uid})")
    
    return "\n".join(lineas)


def registrar_comando_admin(admin_id: str, accion: str, target: Optional[str] = None, resultado: Optional[str] = None) -> None:
    """Registra un comando de administración.
    
    Args:
        admin_id: ID del administrador.
        accion: Acción realizada (add, remove, list).
        target: Objetivo de la acción (user_id o nombre).
        resultado: Resultado de la acción.
    """
    logger = _obtener_logger()
    
    partes = [f"ADMIN", f"admin_id={admin_id}", f"action={accion}"]
    if target:
        partes.append(f"target={target}")
    if resultado:
        partes.append(f"result={resultado}")
    
    mensaje = " | ".join(partes)
    logger.info(mensaje)


def obtener_ruta_config() -> str:
    """Retorna la ruta del archivo de configuración de usuarios."""
    return ARCHIVO_USUARIOS


def obtener_ruta_log() -> str:
    """Retorna la ruta del archivo de log de acceso."""
    return ARCHIVO_LOG
