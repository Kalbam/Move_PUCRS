
# Imagen base ligera con Python 3.10
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de requerimientos y la app
COPY requirements.txt requirements.txt
COPY app_project.py app_project.py
COPY load_data_to_postgres.py load_data_to_postgres.py
COPY df_Ban_Inmet.csv df_Ban_Inmet.csv
COPY df_Hist_Inmet.csv df_Hist_Inmet.csv

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto para Gunicorn
EXPOSE 8050

# Comando de ejecución de la app
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app_project:server"]



