import yt_dlp
from imageio_ffmpeg import get_ffmpeg_exe 
import os
# /*
# yt_dlp depende de FFmpeg para procesar y manipular archivos multimedia, como extraer audio de un video o convertir formatos
# (Se istala un paquete en python [pip install imageio[ffmpeg] ]aunque es mejor por el sistema apt [sudo apt update && sudo apt install ffmpeg])
# */
ffmpeg_path = get_ffmpeg_exe()

def borrar_archivos(nombre=None):
    if nombre == None:
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                file_path = os.path.join(downloads_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"No se pudo borrar el archivo {file_path}: {e}")
    else:
        try:
                    if os.path.isfile(nombre):
                        os.remove(nombre)
        except Exception as e:
                    print(f"No se pudo borrar el archivo {nombre}: {e}")
        
        

def renombrar_archivo(d):
    # Ruta original del archivo
    original_path = d
    
    # Crear la nueva ruta con espacios reemplazados por guiones bajos
    nuevo_path = original_path.replace(' ', '_')
    
    # Renombrar el archivo
    if original_path != nuevo_path:
        os.rename(original_path, nuevo_path)
        (f"Renombrado: {original_path} -> {nuevo_path}")
    return(nuevo_path)


def download_mp3(url):
    try:
        # Borramos los archivos que existan en el directorio:
        yt_opts = {
            'verbose': True,
            'outtmpl': 'downloads/%(title)s.%(ext)s'.replace(' ', '_')# -- Cambiar el nombre del archivo
            ,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': ffmpeg_path,  # Ruta del FFmpeg embebido
        }

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
    except KeyError:
        return("Error,Unable to fetch video information. Please check the video URL or your network connection")
    


# def check_archivo(ruta):
    
#     if os.path.exists(ruta) and os.path.isfile(ruta):
#         return(0)
#     else:
#         return(1)
    
# def borrar_archivo(ruta):
#     if check_archivo(ruta)==0:
#         # Borra el archivo
#         os.remove(ruta)





# print(download_mp3('https://youtu.be/GwxfSmKWX_k'))



















