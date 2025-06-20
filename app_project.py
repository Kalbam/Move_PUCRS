
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os
import numpy as np

# Inicialización de la app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard del Proyecto Final"
server = app.server

# Conexión a PostgreSQL
db_user = os.getenv("POSTGRES_USER")
db_pass = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")
db_name = os.getenv("POSTGRES_DB")

engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")

# Intenta cargar los datos
ban, hist = None, None
try:
    if os.getenv("RENDER", "").lower() == "true":
        ban = pd.read_sql("SELECT * FROM df_ban_inmet", engine)
        hist = pd.read_sql("SELECT * FROM df_hist_inmet", engine)
    else:
        ban = pd.read_csv("df_ban_inmet.csv")
        hist = pd.read_csv("df_hist_inmet.csv")
except Exception as e:
    print("⚠️ No se pudieron cargar los datos:", e)

# Limpieza si se cargaron los datos correctamente
if ban is not None and hist is not None:
    ban = ban.rename(columns={"data_hora": "FECHA_HORA", "RADIACAO GLOBAL(Kj/m²)": "RADIACION"})
    hist = hist.rename(columns={"FECHA_HORA": "FECHA_HORA", "RADIACAO_GLOBAL": "RADIACION"})
    ban["FECHA_HORA"] = pd.to_datetime(ban["FECHA_HORA"])
    hist["FECHA_HORA"] = pd.to_datetime(hist["FECHA_HORA"])

    def limpieza_global(df, col_rad):
        df[col_rad] = (
            df[col_rad].astype(str)
            .replace(["None", "", "nan", "<NA>"], pd.NA)
            .str.replace(",", ".", regex=False)
        )
        df[col_rad] = df[col_rad].str.replace(r"-9999(\.0*)?$", "", regex=True)
        df[col_rad] = df[col_rad].replace("", pd.NA)
        df[col_rad] = pd.to_numeric(df[col_rad], errors="coerce")
        df.loc[df[col_rad] < 0, col_rad] = pd.NA
        return df

    ban = limpieza_global(ban, "RADIACION")
    hist = limpieza_global(hist, "RADIACION")

    # Tabs de metodología y resultados (omitidos aquí por brevedad)
    # Agrega aquí subtabs_metodologia y subtabs_resultados...

    tabs = [
        dcc.Tab(label='1. Introducción', children=[
            html.H2('Introducción'),
            html.P('Aquí se presenta una visión general del contexto de la problemática...')
        ]),
        # Agrega tus demás pestañas...
        dcc.Tab(label='7. Resultados y Análisis Final', children=[
            html.H2('Resultados y Análisis Final'),
            # Asegúrate de haber definido subtabs_resultados
        ]),
    ]

    app.layout = dbc.Container([
        html.H1("Dashboard del Proyecto Final", className="text-center my-4"),
        dcc.Tabs(children=tabs)
    ], fluid=True)

else:
    app.layout = dbc.Container([
        html.H1("Error de conexión o carga de datos", className="text-danger"),
        html.P("No se pudieron cargar los datos desde la base de datos."),
        html.P("Verifique si las tablas df_ban_inmet y df_hist_inmet existen y contienen datos."),
    ])

# Callback sólo si hay datos
if ban is not None and hist is not None:
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
            Input("ciudad-ban",        "value"),
            Input("ciudad-hist",       "value"),
            Input("ciudad-hist-ciudad","value"),
        ],
    )
    def actualizar_panel(ciudad_ban, ciudad_hist_base, ciudad_hist_ciudad):
        ban_clean  = ban.copy()
        hist_clean = hist.copy()

        def indicador(df):
            tot = len(df)
            nulos = df["RADIACION"].isna().sum()
            return f"{tot:,} registros | {nulos / tot * 100:,.1f}% nulos"

        df_b = ban_clean[ban_clean["CIUDAD"] == ciudad_ban]
        indicador_b = indicador(df_b)

        hist_clean["BASE"] = hist_clean["CIUDAD"].str.extract(r"^([A-Z\s]+)")[0].str.strip()
        df_h_base = hist_clean[hist_clean["BASE"] == ciudad_hist_base]
        indicador_h = indicador(df_h_base)

        df_h_ciudad = hist_clean[hist_clean["CIUDAD"] == ciudad_hist_ciudad]
        indicador_h_ciudad = indicador(df_h_ciudad)

        fig_ban = px.line(df_b.sort_values("FECHA_HORA"), x="FECHA_HORA", y="RADIACION", title=f"Radiación BAN – {ciudad_ban}").update_traces(mode="lines", showlegend=False)
        fig_hist = px.line(df_h_base.sort_values("FECHA_HORA"), x="FECHA_HORA", y="RADIACION", color="CIUDAD", title=f"Radiación HIST – {ciudad_hist_base}").update_traces(mode="lines")
        fig_hist_ciudad = px.line(df_h_ciudad.sort_values("FECHA_HORA"), x="FECHA_HORA", y="RADIACION", color="CIUDAD", title=f"Radiación HIST (estación) – {ciudad_hist_ciudad}").update_traces(mode="lines")

        df_nulos_ban = (
            ban_clean.groupby("CIUDAD", group_keys=False)["RADIACION"]
            .apply(lambda s: s.isna().mean() * 100)
            .reset_index(name="% nulos")
            .sort_values("% nulos", ascending=False)
        )
        fig_bar_ban = px.bar(df_nulos_ban, x="% nulos", y="CIUDAD", orientation="h", color="% nulos", color_continuous_scale="Reds").update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

        df_nulos_hist_base = (
            hist_clean.groupby("BASE", group_keys=False)["RADIACION"]
            .apply(lambda s: s.isna().mean() * 100)
            .reset_index(name="% nulos")
            .sort_values("% nulos", ascending=False)
        )
        fig_bar_hist = px.bar(df_nulos_hist_base, x="% nulos", y="BASE", orientation="h", color="% nulos", color_continuous_scale="Reds").update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

        df_nulos_hist_ciudad = (
            hist_clean.groupby("CIUDAD", group_keys=False)["RADIACION"]
            .apply(lambda s: s.isna().mean() * 100)
            .reset_index(name="% nulos")
            .sort_values("% nulos", ascending=False)
        )
        fig_bar_hist_ciudad = px.bar(df_nulos_hist_ciudad, x="% nulos", y="CIUDAD", orientation="h", color="% nulos", color_continuous_scale="Reds").update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

        return (
            fig_ban, fig_hist, fig_hist_ciudad,
            fig_bar_ban, fig_bar_hist, fig_bar_hist_ciudad,
            indicador_b, indicador_h, indicador_h_ciudad
        )

# Ejecutar servidor
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host="0.0.0.0", port=port)

