import pandas as pd
from sqlalchemy import create_engine


db_user = "postgres"
db_password = "KeylaAlba572"
db_host = "db"
db_port = "5432"
db_name = "radiation_inmet"


engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")


# df_ban = pd.read_csv("df_Ban_Inmet.csv")
# df_hist = pd.read_csv("df_Hist_Inmet.csv")


df_ban.to_sql("df_ban_inmet", engine, if_exists="replace", index=False)
df_hist.to_sql("df_hist_inmet", engine, if_exists="replace", index=False)

print(" Datos cargados con éxito en PostgreSQL.")
