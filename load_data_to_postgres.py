import pandas as pd
from sqlalchemy import create_engine

# Parámetros fijos desde Render
db_user = "admin_keyla"
db_pass = "rp49CApKZTEFgAUo3iIsvgz4Ip2Yf9ue"
db_host = "dpg-d1aj7195pdvs73astrmg-a.oregon-postgres.render.com"
db_port = "5432"
db_name = "radiation_inmet"

# Crear conexión SQLAlchemy
engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
)

# Cargar los archivos CSV
df_ban = pd.read_csv("df_ban_inmet.csv")
df_hist = pd.read_csv("df_hist_inmet.csv")

# Cargar los datos a la base de datos en Render
try:
    df_ban.to_sql("df_ban_inmet", engine, if_exists="replace", index=False)
    print("✅ Cargado: df_ban_inmet")
except Exception as e:
    print("❌ Error en df_ban_inmet:", e)

try:
    df_hist.to_sql("df_hist_inmet", engine, if_exists="replace", index=False)
    print("✅ Cargado: df_hist_inmet")
except Exception as e:
    print("❌ Error en df_hist_inmet:", e)

