#!/usr/bin/env python3
import os
import sys
import multiprocessing
import asyncio
import threading
import time

os.chdir('/app')

from dotenv import load_dotenv
load_dotenv()

MODO = os.environ.get('MODO', 'ambos').lower()

def limpieza_periodica():
    from gestion_download import borrar_archivos
    while True:
        time.sleep(600)
        print("[LIMPIEZA] Borrando archivos antiguos...")
        borrar_archivos()

def proceso_flask():
    from app import app
    print("[FLASK] Iniciando servidor web...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def proceso_telegram():
    import nest_asyncio
    nest_asyncio.apply()
    from telegram_bot import iniciar_bot
    print("[TELEGRAM] Iniciando bot...")
    asyncio.run(iniciar_bot())

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn', force=True)
    
    print(f"[MAIN] Modo de ejecución: {MODO}")
    
    hilo_limpieza = threading.Thread(target=limpieza_periodica, daemon=True)
    hilo_limpieza.start()
    print("[MAIN] Hilo de limpieza iniciado")
    
    procesos = []
    
    if MODO in ('web', 'ambos'):
        p_flask = multiprocessing.Process(target=proceso_flask, name='flask')
        p_flask.start()
        procesos.append(p_flask)
        print("[MAIN] Servicio Flask iniciado")
    
    if MODO in ('telegram', 'ambos'):
        p_telegram = multiprocessing.Process(target=proceso_telegram, name='telegram')
        p_telegram.start()
        procesos.append(p_telegram)
        print("[MAIN] Servicio Telegram iniciado")
    
    if not procesos:
        print("[MAIN] ERROR: No hay servicios configurados. MODO debe ser: telegram, web o ambos")
        sys.exit(1)
    
    print("[MAIN] Todos los servicios iniciados")
    
    try:
        procesos[0].join()
    except KeyboardInterrupt:
        print("[MAIN] Apagando...")
        for p in procesos:
            p.terminate()
        sys.exit(0)
