import pandas as pd
from sqlalchemy import create_engine


# db_user = "postgres"
# db_password = "KeylaAlba572"
# db_host = "db"
# db_port = "5432"
# db_name = "radiation_inmet"

# engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# df_ban = pd.read_csv("df_Ban_Inmet.csv")
# df_hist = pd.read_csv("df_Hist_Inmet.csv")

# df_ban.to_sql("df_ban_inmet", engine, if_exists="replace", index=False)
# df_hist.to_sql("df_hist_inmet", engine, if_exists="replace", index=False)



# print(" Datos cargados con éxito en PostgreSQL.")
# db_user = "radiation_inmet_db_v1_user"
# db_password = "5EshSNxUVp7iJIEX8ZLFA7miiGgcQeOJ"
# db_host = "dpg-d1d2ptqdbo4c73cb2j00-a.oregon-postgres.render.com"
# db_port = "5432"
# db_name = "radiation_inmet_db_v1"

# Crear motor de conexión a Render
db_url = "postgresql://radiation_inmet_db_v1_user:5EshSNxUVp7iJIEX8ZLFA7miiGgcQeOJ@dpg-d1d2ptqdbo4c73cb2j00-a:5432/radiation_inmet_db_v1"

# Crear el engine
engine = create_engine(db_url)

try:
    # Leer archivos locales (asegúrate que estén en la misma carpeta cuando ejecutes esto localmente)
    df_ban = pd.read_csv("df_Ban_Inmet.csv", encoding="utf-8-sig")
    df_hist = pd.read_csv("df_Hist_Inmet.csv", encoding="utf-8-sig")

    # Subir a PostgreSQL
    df_ban.to_sql("df_ban_inmet", engine, if_exists="replace", index=False)
    df_hist.to_sql("df_hist_inmet", engine, if_exists="replace", index=False)

    print(" Datos cargados con éxito en PostgreSQL Render.")

except FileNotFoundError as e:
    print(f" Archivo no encontrado: {e.filename}")

except Exception as e:
    print(f" Error inesperado: {e}")
