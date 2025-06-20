
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os
import numpy as np
from functools import lru_cache

# ═════════════════════════════
# 1) Dash – Bootstrap
# ═════════════════════════════
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title  = "Dashboard del Proyecto Final"
server = app.server

# ═════════════════════════════
# 2) Conexión a la BD
# ═════════════════════════════
db_user = os.getenv("POSTGRES_USER")
db_pass = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB")

engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
)

# ═════════════════════════════
# 3) Función de limpieza común
# ═════════════════════════════
def limpieza_global(df: pd.DataFrame, col_rad: str) -> pd.DataFrame:
    df[col_rad] = (
        df[col_rad]
        .astype(str)
        .replace(["None", "", "nan", "<NA>"], pd.NA)
        .str.replace(",", ".", regex=False)
        .str.replace(r"-9999(\.0*)?$", "", regex=True)
        .replace("", pd.NA)
    )
    df[col_rad] = pd.to_numeric(df[col_rad], errors="coerce")
    df.loc[df[col_rad] < 0, col_rad] = pd.NA
    return df

# ═════════════════════════════
# 4) Cargamos datos bajo demanda
#    • En Render: desde PostgreSQL
#    • En local : desde CSV
#    • Cacheados en memoria
# ═════════════════════════════
@lru_cache(maxsize=1)          # evita repetir lecturas cada callback
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if os.getenv("RENDER", "").lower() == "true":          # producción
        ban  = pd.read_sql("SELECT * FROM df_ban_inmet",  engine)
        hist = pd.read_sql("SELECT * FROM df_hist_inmet", engine)
    else:                                                  # local
        ban  = pd.read_csv("df_ban_inmet.csv")
        hist = pd.read_csv("df_hist_inmet.csv")

    # Renombrar y convertir fechas
    ban  = ban.rename(columns={"data_hora": "FECHA_HORA",
                               "RADIACAO GLOBAL(Kj/m²)": "RADIACION"})
    hist = hist.rename(columns={"FECHA_HORA": "FECHA_HORA",
                                "RADIACAO_GLOBAL": "RADIACION"})

    ban["FECHA_HORA"]  = pd.to_datetime(ban["FECHA_HORA"],  errors="coerce")
    hist["FECHA_HORA"] = pd.to_datetime(hist["FECHA_HORA"], errors="coerce")

    # Limpieza
    ban  = limpieza_global(ban,  "RADIACION")
    hist = limpieza_global(hist, "RADIACION")

    return ban, hist

# ═════════════════════════════
# 5) Layout (idéntico al tuyo)
# ═════════════════════════════
# --- se omite la parte larga del layout para ahorrar espacio ---
#   (No cambié nada; copia-pega tu definición de `subtabs_metodologia`,
#    `subtabs_resultados`, `tabs`, y el `app.layout`)

# ……………………………………………………………………………………………………………………………
# Usa la misma definición de subtabs_metodologia, subtabs_resultados,
# la lista `tabs` y el `app.layout` que pegaste. No requiere cambios.
# ……………………………………………………………………………………………………………………………

# ═════════════════════════════
# 6) Callback principal
# ═════════════════════════════
@app.callback(
    [
        Output("line-ban",             "figure"),
        Output("line-hist",            "figure"),
        Output("line-hist-ciudad",     "figure"),
        Output("bar-nulos-ban",        "figure"),
        Output("bar-nulos-hist",       "figure"),
        Output("bar-nulos-hist-ciudad","figure"),
        Output("count-ban",            "children"),
        Output("count-hist",           "children"),
        Output("count-hist-ciudad",    "children"),
    ],
    [
        Input("ciudad-ban", "value"),
        Input("ciudad-hist", "value"),
        Input("ciudad-hist-ciudad", "value"),
    ],
)
def actualizar_panel(ciudad_ban, ciudad_hist_base, ciudad_hist_ciudad):
    ### CAMBIO ↓↓↓   obtenemos datos cada vez (cacheados)
    ban, hist = get_data()

    hist["BASE"] = hist["CIUDAD"].str.extract(r"^([A-Z\s]+)")[0].str.strip()

    # --- filtros ---
    df_b        = ban[ban["CIUDAD"] == ciudad_ban]
    df_h_base   = hist[hist["BASE"]   == ciudad_hist_base]
    df_h_ciudad = hist[hist["CIUDAD"] == ciudad_hist_ciudad]

    # --- indicadores ---
    def indicador(df):
        return f"{df.shape[0]:,} registros | {df['RADIACION'].isna().mean()*100:,.1f}% nulos"

    indicador_b         = indicador(df_b)
    indicador_h         = indicador(df_h_base)
    indicador_h_ciudad  = indicador(df_h_ciudad)

    # --- gráficas de línea ---
    fig_ban = px.line(df_b.sort_values("FECHA_HORA"),
                      x="FECHA_HORA", y="RADIACION",
                      title=f"Radiación BAN – {ciudad_ban}") \
               .update_traces(mode="lines", showlegend=False)

    fig_hist = px.line(df_h_base.sort_values("FECHA_HORA"),
                       x="FECHA_HORA", y="RADIACION", color="CIUDAD",
                       title=f"Radiación HIST – {ciudad_hist_base}") \
                .update_traces(mode="lines")

    fig_hist_ciudad = px.line(df_h_ciudad.sort_values("FECHA_HORA"),
                              x="FECHA_HORA", y="RADIACION", color="CIUDAD",
                              title=f"Radiación HIST (estación) – {ciudad_hist_ciudad}") \
                       .update_traces(mode="lines")

    # --- barras de % nulos ---
    def graf_barra(df, grupo, titulo):
        tmp = (df.groupby(grupo)["RADIACION"]
                .apply(lambda s: s.isna().mean()*100)
                .reset_index(name="% nulos")
                .sort_values("% nulos", ascending=False))
        return px.bar(tmp, x="% nulos", y=grupo, orientation="h",
                      color="% nulos", color_continuous_scale="Reds",
                      title=titulo).update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

    fig_bar_ban         = graf_barra(ban,  "CIUDAD", "% de valores nulos por ciudad (BAN)")
    fig_bar_hist        = graf_barra(hist, "BASE",   "% de valores nulos por ciudad base (HIST)")
    fig_bar_hist_ciudad = graf_barra(hist, "CIUDAD", "% de valores nulos por estación completa (HIST)")

    return (
        fig_ban, fig_hist, fig_hist_ciudad,
        fig_bar_ban, fig_bar_hist, fig_bar_hist_ciudad,
        indicador_b, indicador_h, indicador_h_ciudad
    )

# ═════════════════════════════
# 7) Lanzar la app
# ═════════════════════════════
if __name__ == "__main__":
    app.run_server(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8050)),
        debug=False               # pon True si necesitas ver errores en local
    )
