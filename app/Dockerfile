# Usa una imagen base con Python y pip
FROM python:3.9-slim
MAINTAINER IgnacioGovantes "ignaciogovo@gmail.com"

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de tu proyecto al contenedor
COPY . /app

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir flask
RUN pip install --no-cache-dir imageio[ffmpeg]
RUN pip install --no-cache-dir yt_dlp



# Exponer el puerto 5000
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]

