import os
import queue
import threading
import asyncio
import time
from dotenv import load_dotenv
from gestion_download import download_mp3
from cola_logs import log_agregar, log_procesar, log_completar, log_obtener_posicion, log_cola_vacia, log_avance_cola

load_dotenv()

MAX_COLA = int(os.environ.get('MAX_COLA_DESCARGAS', 50))


class SolicitudDescarga:
    def __init__(self, user_id, url, formato, callback=None):
        self.user_id = user_id
        self.url = url
        self.formato = formato
        self.callback = callback
        self.resultado = None
        self.evento_listo = threading.Event()
        self.estado_callback = None
        self.posicion = None


class ColaDescargas:
    def __init__(self, nombre_cola="cola"):
        self.cola = queue.Queue()
        self.solicitudes = {}
        self.lock = threading.Lock()
        self.worker_activo = False
        self.worker_thread = None
        self.contador_posicion = 0
        self.nombre_cola = nombre_cola

    def obtener_posicion(self, user_id):
        with self.lock:
            for sol in self.cola.queue:
                if sol.user_id == user_id:
                    log_obtener_posicion(user_id, sol.posicion, self.nombre_cola)
                    return sol.posicion
            
            if user_id in self.solicitudes:
                posicion = self.solicitudes[user_id].posicion
                log_obtener_posicion(user_id, posicion, self.nombre_cola)
                return posicion
            
            log_obtener_posicion(user_id, -1, self.nombre_cola)
            return -1

    def agregar(self, user_id, url, formato, callback=None, estado_callback=None):
        with self.lock:
            solicitudes_activas = self.cola.qsize()
            
            if solicitudes_activas >= MAX_COLA:
                log_agregar(user_id, url, formato, -1, self.nombre_cola)
                return False, "La cola está llena. Intenta más tarde."
            
            self.contador_posicion += 1
            posicion = self.contador_posicion - 1
        
        solicitud = SolicitudDescarga(user_id, url, formato, callback)
        solicitud.posicion = posicion
        solicitud.estado_callback = estado_callback
        
        with self.lock:
            self.solicitudes[user_id] = solicitud
        
        self.cola.put(solicitud)
        
        log_agregar(user_id, url, formato, posicion, self.nombre_cola)
        
        if not self.worker_activo:
            self.worker_activo = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
        
        return True, posicion

    def _worker(self):
        while True:
            solicitud_a_procesar = None
            
            with self.lock:
                items = list(self.cola.queue)
                for sol in items:
                    if sol.posicion == 0:
                        solicitud_a_procesar = sol
                        break
            
            if solicitud_a_procesar is None:
                with self.lock:
                    if self.cola.empty():
                        self.worker_activo = False
                        self.contador_posicion = 0
                        log_cola_vacia(self.nombre_cola)
                        break
                    if self.cola.qsize() > 0:
                        first_sol = list(self.cola.queue)[0]
                        first_sol.posicion = 0
                        log_avance_cola(first_sol.user_id, first_sol.posicion, 0, self.nombre_cola)
                time.sleep(0.5)
                continue
            
            for _ in range(self.cola.qsize()):
                self.cola.get()
            
            for sol in list(self.cola.queue):
                posicion_anterior = sol.posicion
                sol.posicion -= 1
                log_avance_cola(sol.user_id, posicion_anterior, sol.posicion, self.nombre_cola)
                if sol.estado_callback:
                    try:
                        sol.estado_callback("avance_cola", posicion=sol.posicion)
                    except Exception as e:
                        print(f"[{self.nombre_cola}] Error en estado_callback avance_cola: {e}")
            
            user_id = solicitud_a_procesar.user_id
            url = solicitud_a_procesar.url
            formato = solicitud_a_procesar.formato
            callback = solicitud_a_procesar.callback
            estado_callback = getattr(solicitud_a_procesar, 'estado_callback', None)
            
            log_procesar(user_id, url, self.nombre_cola)

            try:
                archivo = download_mp3(url, formato)
            except Exception as e:
                archivo = f"Error: {str(e)}"
            
            log_completar(user_id, archivo, self.nombre_cola)

            if estado_callback:
                try:
                    estado_callback("completado", archivo=archivo)
                except Exception as e:
                    print(f"[{self.nombre_cola}] Error en estado_callback completado: {e}")

    def esperar_resultado(self, user_id, timeout=600):
        with self.lock:
            if user_id not in self.solicitudes:
                return None
            solicitud = self.solicitudes[user_id]
        
        solicitud.evento_listo.wait(timeout=timeout)
        return solicitud.resultado


cola_descargas = ColaDescargas(nombre_cola="cola")
