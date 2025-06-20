# Dashboard de Radiación INMET 🌞

Este proyecto permite visualizar la radiación solar histórica en distintas ciudades usando un dashboard desarrollado con Dash y desplegado con Docker.

---

## 📁 Estructura del Proyecto

- `app_project.py`: Aplicación principal en Dash.
- `Dockerfile`: Imagen para construir el contenedor del dashboard.
- `docker-compose.yml`: Orquestador de servicios para PostgreSQL + dashboard.
- `requirements.txt`: Librerías necesarias.
- `wait-for-it.sh`: Script que espera a que PostgreSQL esté listo.
- `load_data_to_postgres.py`: Script para cargar los datos desde archivos `.csv` a la base de datos.
- `Procfile`: Archivo de proceso (opcional para despliegues externos).

---

## 🚀 Instrucciones para Ejecutar

### 1. Clonar o extraer este proyecto en una carpeta

```bash
unzip dashboard_radiation_project.zip
cd dashboard_radiation_project
```

### 2. Agregar los archivos de datos

Coloca los siguientes archivos `.csv` junto a los demás archivos:

- `df_Ban_Inmet.csv`
- `df_Hist_Inmet.csv`

> Asegúrate de que estos archivos coincidan con los nombres esperados en `load_data_to_postgres.py`.

---

### 3. Construir y levantar el proyecto

```bash
docker-compose up --build
```

Esto hará lo siguiente:

- Iniciará un contenedor PostgreSQL con la base `radiation_inmet`.
- Construirá la app Dash.
- Esperará a que la base esté lista.
- Ejecutará el dashboard en: [http://localhost:8050](http://localhost:8050)

---

### 4. Cargar los datos manualmente (si es necesario)

En caso de error por tabla no encontrada, puedes cargar los datos ejecutando:

```bash
docker exec -it dashboard-radiation-app python load_data_to_postgres.py
```

---

## 🛑 Para detener todo

```bash
docker-compose down
```

---

## ✅ Requisitos

- Docker
- Docker Compose

---

Proyecto adaptable para despliegue en Linux. Desarrollado por Keyla Vanessa Alba Molina.
