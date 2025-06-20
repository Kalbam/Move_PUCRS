
# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia solo los archivos necesarios
COPY requirements.txt .
COPY app_project.py .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto donde se ejecuta Dash
EXPOSE 8050

# Comando para ejecutar la app con Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app_project:server"]

