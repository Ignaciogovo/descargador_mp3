from flask import Flask, request, render_template_string, send_file,render_template
import os
from gestion_download import download_mp3

app = Flask(__name__)

# Ruta principal con el formularios
@app.route('/', methods=['GET', 'POST'])
def formulario():
    mensaje = ""
    enlace_descarga = None

    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            # Llama a la función para procesar la URL
            archivo_generado = download_mp3(url)

            # Guarda el enlace para la descarga
            enlace_descarga = f"/descargar?archivo={archivo_generado}"
            mensaje = "Archivo generado correctamente. Puedes descargarlo a continuación."
        else:
            mensaje = "Por favor, introduce una URL válida."

    return render_template('index.html', mensaje=mensaje, enlace_descarga=enlace_descarga)

# Ruta para descargar el archivo
@app.route('/descargar')
def descargar():
    archivo = request.args.get('archivo')
    if archivo and os.path.exists(archivo):
        return send_file(archivo, as_attachment=True)
    else:
        return "Archivo no encontrado", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')