import logging
import os


def setup_logger(name='cola'):
    """Configura un logger que escribe en archivo y consola"""
    
    log_dir = os.environ.get('LOG_DIR', '/app/logs')
    log_file = os.path.join(log_dir, 'cola_descargas.log')
    
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except:
            log_file = '/tmp/cola_descargas.log'
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | [%(colatype)s] | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

cola_logger = setup_logger('cola')


def log_agregar(user_id, url, formato, posicion, nombre_cola="cola"):
    """Log cuando se agrega una descarga a la cola"""
    extra = {'colatype': nombre_cola}
    cola_logger.info(
        f"AGREGAR | user_id={user_id} | url={url[:50]}... | formato={formato} | posicion={posicion}",
        extra=extra
    )


def log_procesar(user_id, url, nombre_cola="cola"):
    """Log cuando el worker empieza a procesar"""
    extra = {'colatype': nombre_cola}
    cola_logger.info(
        f"PROCESAR | user_id={user_id} | url={url[:50]}...",
        extra=extra
    )


def log_completar(user_id, archivo, nombre_cola="cola"):
    """Log cuando se completa una descarga"""
    extra = {'colatype': nombre_cola}
    if archivo and not archivo.startswith("Error:"):
        cola_logger.info(
            f"COMPLETAR | user_id={user_id} | archivo={archivo}",
            extra=extra
        )
    else:
        cola_logger.error(
            f"ERROR | user_id={user_id} | archivo={archivo}",
            extra=extra
        )


def log_obtener_posicion(user_id, posicion, nombre_cola="cola"):
    """Log cuando se consulta la posición"""
    extra = {'colatype': nombre_cola}
    cola_logger.debug(
        f"POSICION | user_id={user_id} | posicion={posicion}",
        extra=extra
    )


def log_cola_vacia(nombre_cola="cola"):
    """Log cuando la cola queda vacía"""
    extra = {'colatype': nombre_cola}
    cola_logger.info("COLA_VACIA | El worker se detiene", extra=extra)


def log_avance_cola(user_id, posicion_anterior, posicion_nueva, nombre_cola="cola"):
    """Log cuando una descarga avanza en la cola"""
    extra = {'colatype': nombre_cola}
    cola_logger.info(
        f"AVANCE_COLA | user_id={user_id} | de={posicion_anterior} a={posicion_nueva}",
        extra=extra
    )
