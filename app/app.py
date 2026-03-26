from flask import Flask, request, render_template_string, send_file,render_template, jsonify
import os
import threading
import time
from dotenv import load_dotenv
from gestion_download import download_mp3,borrar_archivos
from cola_descargas import cola_descargas

load_dotenv()

app = Flask(__name__)

estados_descarga = {}

def estado_callback_web(estado, session_id, **kwargs):
    if session_id in estados_descarga:
        posicion = kwargs.get('posicion', 0)
        
        if estado == "en_cola":
            estados_descarga[session_id]['estado'] = 'en_cola'
            estados_descarga[session_id]['posicion'] = posicion
        elif estado == "avance_cola":
            estados_descarga[session_id]['estado'] = 'avance_cola'
            estados_descarga[session_id]['posicion'] = posicion
        elif estado == "descargando":
            estados_descarga[session_id]['estado'] = 'descargando'
            estados_descarga[session_id]['posicion'] = 0
        elif estado == "completado":
            archivo = kwargs.get('archivo', '')
            if archivo and not archivo.startswith("Error:"):
                estados_descarga[session_id] = {
                    'estado': 'completado', 
                    'posicion': 0, 
                    'archivo': archivo
                }
            else:
                estados_descarga[session_id] = {
                    'estado': 'error', 
                    'posicion': 0, 
                    'archivo': archivo or 'Error desconocido'
                }

@app.route('/', methods=['GET', 'POST'])
def formulario():
    mensaje = ""
    posicion_cola = None
    session_id = None

    if request.method == 'POST':
        url = request.form.get('url')
        formato = request.form.get('formato')

        if url:
            session_id = f"web_{request.remote_addr}_{int(time.time())}"
            estados_descarga[session_id] = {'estado': 'en_cola', 'posicion': 0, 'archivo': None}
            
            def callback_estado(estado, **kwargs):
                estado_callback_web(estado, session_id, **kwargs)
            
            exito, posicion = cola_descargas.agregar(session_id, url, formato, estado_callback=callback_estado)
            
            if not exito:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': posicion})
                mensaje = posicion
            else:
                posicion_cola = posicion
                estados_descarga[session_id]['posicion'] = posicion
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'session_id': session_id, 'posicion': posicion})
                
                if posicion == 0:
                    mensaje = "Tu descarga está siendo procesada..."
                else:
                    mensaje = f"Tu descarga está en cola. Posición: {posicion}"

    return render_template('index.html', mensaje=mensaje, posicion_cola=posicion_cola, session_id=session_id)

@app.route('/estado_descarga')
def estado_descarga():
    session_id = request.args.get('session_id')
    if session_id and session_id in estados_descarga:
        data = estados_descarga[session_id].copy()
        
        posicion_real = cola_descargas.obtener_posicion(session_id)
        
        if posicion_real == 0:
            data['estado'] = 'descargando'
            data['posicion'] = 1
        elif posicion_real > 0:
            data['estado'] = 'en_cola'
            data['posicion'] = posicion_real
        elif data['estado'] not in ('completado', 'error'):
            data['estado'] = 'desconocido'
        
        if data['estado'] == 'completado' and data['archivo']:
            data['archivo'] = f"/descargar?archivo={data['archivo']}"
        return jsonify(data)
    return jsonify({'estado': 'desconocido'})

@app.route('/descargar')
def descargar():
    archivo = request.args.get('archivo')
    if archivo and os.path.exists(archivo):
        return send_file(archivo, as_attachment=True)
    else:
        return "Archivo no encontrado: "+str(archivo), 404
