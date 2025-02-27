import yt_dlp
from imageio_ffmpeg import get_ffmpeg_exe 
import os
import time
import re


# /*
# yt_dlp depende de FFmpeg para procesar y manipular archivos multimedia, como extraer audio de un video o convertir formatos
# (Se istala un paquete en python [pip install imageio[ffmpeg] ]aunque es mejor por el sistema apt [sudo apt update && sudo apt install ffmpeg])
# */
ffmpeg_path = get_ffmpeg_exe()

def borrar_archivos(nombre=None):

    if nombre == None: #-- Se borran los archivos creados después de dos horas
        # Tiempo actual en segundos
        tiempo_actual = time.time()
        # Tiempo límite (1 hora = 3600 segundos)
        limite_tiempo = tiempo_actual - 7200     
        #Carpeta donde se encuentran las descargas        
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                file_path = os.path.join(downloads_dir, file)
                try:
                    if os.path.isfile(file_path):
                        tiempo_creacion = os.path.getctime(file_path)
                        if limite_tiempo > tiempo_creacion:
                            os.remove(file_path)
                            print(f"Borrado archivo max 2 horas: {file_path}")
                except Exception as e:
                    print(f"No se pudo borrar el archivo {file_path}: {e}")
    else:
        try:
                    if os.path.isfile(nombre):
                        os.remove(nombre)
        except Exception as e:
                    print(f"No se pudo borrar el archivo {nombre}: {e}")
        

def renombrar_archivo(original_path):    
    # Remplazamos todos los simbolos que puedan generar problemas con la ruta
    patron = r'[:*?"<>|~#¬｜ &]'
    nuevo_path = re.sub(patron, '_', re.sub(r'\|', '_', original_path))
    
    # Renombrar el archivo
    if original_path != nuevo_path:
        os.rename(original_path, nuevo_path)
        (f"Renombrado: {original_path} -> {nuevo_path}")
    return(nuevo_path)


def download_mp3(url,formato='mp3'):
    #Mecanismo de seguridad para borrar archivos anteriores a 2 horas:
    borrar_archivos() 
    
    try:
        # Configuración general
        yt_opts = {
            'verbose': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s'.replace(' ', '_'),# -- Cambiar el nombre del archivo
            'ffmpeg_location': ffmpeg_path,  # Ruta del FFmpeg embebido
        }

        # Si el formato es MP3 (descargar solo audio)
        if formato.lower() == "mp3":
            yt_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        # Si el formato es MP4 (descargar video + audio)
        elif formato.lower() == "mp4":
            yt_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })

        ydl = yt_dlp.YoutubeDL(yt_opts)
        info_dict = ydl.extract_info(url, download=True)
        
       # Obtener el archivo final (después del postprocesamiento)
        try:
            # Busca el archivo procesado en los metadatos
            file_path = info_dict['requested_downloads'][0]['filepath']
        except (KeyError, IndexError):
            # Si no se encuentra, devuelve el archivo original como fallback
            file_path = ydl.prepare_filename(info_dict)

        file_path = renombrar_archivo(file_path)
        return(file_path)
    except Exception as e:
        print(e)
        return("Error,Unable to fetch video information. Please check the video URL or your network connection")
    




#pruebas
if __name__ == '__main__':
    print(download_mp3('https://youtu.be/jRxrb_EtzQQ','mp3'))



















