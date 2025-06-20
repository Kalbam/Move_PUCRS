
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
app.title = "Dashboard del Proyecto Final "
server = app.server

# Conexión a PostgreSQL
db_user = os.getenv("POSTGRES_USER")
db_pass = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")  
db_port = os.getenv("POSTGRES_PORT")
db_name = os.getenv("POSTGRES_DB")

engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")


if os.getenv("RENDER", "").lower() == "true":
    # Entorno producción: usar PostgreSQL
    ban = pd.read_sql("SELECT * FROM df_ban_inmet", engine)
    hist = pd.read_sql("SELECT * FROM df_hist_inmet", engine)
else:
    # Entorno local: usar CSV
    ban = pd.read_csv("df_ban_inmet.csv")
    hist = pd.read_csv("df_hist_inmet.csv")


ban = ban.rename(columns={"data_hora": "FECHA_HORA", "RADIACAO GLOBAL(Kj/m²)": "RADIACION"})
hist = hist.rename(columns={"FECHA_HORA": "FECHA_HORA", "RADIACAO_GLOBAL": "RADIACION"})

ban["FECHA_HORA"] = pd.to_datetime(ban["FECHA_HORA"])
hist["FECHA_HORA"] = pd.to_datetime(hist["FECHA_HORA"])


def limpieza_global(df, col_rad):
    df[col_rad] = (
        df[col_rad]
        .astype(str)
        .replace(["None", "", "nan", "<NA>"], pd.NA)
        .str.replace(",", ".", regex=False)
    )
    # Reemplazo corregido: el resultado de .str.replace debe ser string o función
    df[col_rad] = df[col_rad].str.replace(r"-9999(\.0*)?$", "", regex=True)
    df[col_rad] = df[col_rad].replace("", pd.NA)

    df[col_rad] = pd.to_numeric(df[col_rad], errors="coerce")
    df.loc[df[col_rad] < 0, col_rad] = pd.NA
    return df


ban  = limpieza_global(ban,  "RADIACION")
hist = limpieza_global(hist, "RADIACION")

# Subpestañas de metodología
subtabs_metodologia = dcc.Tabs([
    dcc.Tab(label='a. Definición del Problema', children=[
        html.H4('a. Definición del Problema a Resolver'),
        html.Ul([
            html.Li('Tipo de problema: clasificación / regresión / agrupamiento / series de tiempo'),
            html.Li('Variable objetivo o de interés: Nombre de la variable')
        ])
    ]),
    dcc.Tab(label='b. Preparación de Datos', children=[
        html.H4('b. Preparación de los Datos'),
        html.Ul([
            html.Li('Limpieza y transformación de datos'),
            html.Li('División del dataset en entrenamiento y prueba o validación cruzada')
        ])
    ]),
    dcc.Tab(label='c. Selección del Modelo', children=[
        html.H4('c. Selección del Modelo o Algoritmo'),
        html.Ul([
            html.Li('Modelo(s) seleccionados'),
            html.Li('Justificación de la elección'),
            html.Li('Ecuación o representación matemática si aplica')
        ])
    ]),
    dcc.Tab(label='d. Evaluación del Modelo', children=[
        html.H4('d. Entrenamiento y Evaluación del Modelo'),
        html.Ul([
            html.Li('Proceso de entrenamiento'),
            html.Li('Métricas de evaluación: RMSE, MAE, Accuracy, etc.'),
            html.Li('Validación utilizada')
        ])
    ])
])

# ──────────────────────────────────────────────────────────────────────
subtabs_resultados = dcc.Tabs(
    [
        dcc.Tab(
            label="a. EDA",
            children=[
                html.H4("a. Análisis Exploratorio de Datos (EDA)"),

                # ───────── Indicadores ─────────
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardHeader("Total registros BAN (ciudad)"),
                        dbc.CardBody(html.H4(id="count-ban", className="card-title mb-0")),
                    ], color="primary", inverse=True), width=4),

                    dbc.Col(dbc.Card([
                        dbc.CardHeader("Total registros HIST (ciudad base)"),
                        dbc.CardBody(html.H4(id="count-hist", className="card-title mb-0")),
                    ], color="info", inverse=True), width=4),

                    dbc.Col(dbc.Card([
                        dbc.CardHeader("Total registros HIST (ciudad completa)"),
                        dbc.CardBody(html.H4(id="count-hist-ciudad", className="card-title mb-0")),
                    ], color="danger", inverse=True), width=4),
                ], className="mb-4"),

                # ───────── Filtros ─────────
                dbc.Row([
                    # BAN
                    dbc.Col([
                        html.Label("Ciudad (df_ban_inmet)"),
                        dcc.Dropdown(
                            id="ciudad-ban",
                            options=[{"label": c, "value": c} for c in sorted(ban["CIUDAD"].unique())],
                            value=sorted(ban["CIUDAD"].unique())[0],
                            clearable=False,
                        ),
                    ], width=4),

                    # HIST agrupado por BASE (sin altitud)
                    dbc.Col([
                        html.Label("Ciudad base (df_hist_inmet, agrupado)"),
                        dcc.Dropdown(
                            id="ciudad-hist",
                            options=[{"label": base, "value": base}
                                     for base in sorted(
                                         hist["CIUDAD"]
                                             .str.extract(r"^([A-Z\s]+)")[0]
                                             .dropna()
                                             .unique()
                                     )],
                            value=sorted(
                                hist["CIUDAD"]
                                    .str.extract(r"^([A-Z\s]+)")[0]
                                    .dropna()
                                    .unique()
                            )[0],
                            clearable=False,
                        ),
                    ], width=4),

                    # HIST por ciudad completa (con Alt)
                    dbc.Col([
                        html.Label("Ciudad completa (df_hist_inmet, con altitud)"),
                        dcc.Dropdown(
                            id="ciudad-hist-ciudad",
                            options=[{"label": c, "value": c} for c in sorted(hist["CIUDAD"].unique())],
                            value=sorted(hist["CIUDAD"].unique())[0],
                            clearable=False,
                        ),
                    ], width=4),
                ], className="mb-3"),

                # ───────── Gráficos de líneas ─────────
                dbc.Row([
                    dbc.Col([
                        html.H5("Radiación BAN (por ciudad)"),
                        dcc.Graph(id="line-ban"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("Radiación HIST (agrupado por ciudad base)"),
                        dcc.Graph(id="line-hist"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("Radiación HIST (por ciudad completa con altitud)"),
                        dcc.Graph(id="line-hist-ciudad"),
                    ], lg=4, width=12),
                ]),

                html.Hr(),

                # ───────── Gráficos de barras ─────────
                html.H4("Gráfico de % de valores nulos", className="my-4 text-center"),
                dbc.Row([
                    dbc.Col([
                        html.H5("% de valores nulos por ciudad (BAN)", className="text-center"),
                        dcc.Graph(id="bar-nulos-ban"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("% de valores nulos por ciudad base (HIST)", className="text-center"),
                        dcc.Graph(id="bar-nulos-hist"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("% de valores nulos por estación completa (HIST)", className="text-center"),
                        dcc.Graph(id="bar-nulos-hist-ciudad"),
                    ], lg=4, width=12),
                ]),
            ]
        ),

        # ───────── Pestañas b-e sin cambios ─────────
        dcc.Tab(label="b. EDA 2", children=[
            html.H4("b. EDA 2 – Análisis adicional"),
            html.P("Aquí puedes incluir análisis exploratorios complementarios como segmentaciones, box-plots, histogramas comparativos o mapas."),
        ]),

        dcc.Tab(label="c. Visualización del Modelo", children=[
            html.H4("c. Visualización de Resultados del Modelo"),
            html.P("Aquí se mostrarán las métricas de evaluación de los modelos en forma de tabla."),
            html.Ul([
                html.Li("Gráficas de comparación: valores reales vs. predichos"),
                html.Li("Análisis de residuales"),
            ]),
        ]),

        dcc.Tab(label="d. Indicadores del Modelo", children=[
            html.H4("d. Indicadores de Evaluación del Modelo"),
            html.Ul([
                html.Li("Tabla de errores: RMSE, MAE, MSE, etc."),
                html.Li("Interpretación de los valores para comparar modelos"),
            ]),
        ]),

        dcc.Tab(label="e. Limitaciones", children=[
            html.H4("e. Limitaciones y Consideraciones Finales"),
            html.Ul([
                html.Li("Restricciones del análisis"),
                html.Li("Posibles mejoras futuras"),
            ]),
        ]),
    ]
)



tabs = [
    dcc.Tab(label='1. Introducción', children=[
        html.H2('Introducción'),
        html.P('Aquí se presenta una visión general del contexto de la problemática, el análisis realizado y los hallazgos encontrados.'),
        html.P('De manera resumida, indicar lo que se pretende lograr con el proyecto')
    ]),
    dcc.Tab(label='2. Contexto', children=[
        html.H2('Contexto'),
        html.P('Descripción breve del contexto del proyecto.'),
        html.Ul([
            html.Li('Fuente de los datos: Nombre de la fuente'),
            html.Li('Variables de interés: listar variables-operacionalización')
        ])
    ]),
    dcc.Tab(label='3. Planteamiento del Problema', children=[
        html.H2('Planteamiento del Problema'),
        html.P('Describe en pocas líneas la problemática abordada.'),
        html.P('Pregunta problema: ¿Cuál es la pregunta que intenta responder el análisis?')
    ]),
    dcc.Tab(label='4. Objetivos y Justificación', children=[
        html.H2('Objetivos y Justificación'),
        html.H4('Objetivo General'),
        html.Ul([html.Li('Objetivo general del proyecto')]),
        html.H4('Objetivos Específicos'),
        html.Ul([
            html.Li('Objetivo específico 1'),
            html.Li('Objetivo específico 2'),
            html.Li('Objetivo específico 3')
        ]),
        html.H4('Justificación'),
        html.P('Explicación breve sobre la importancia de abordar el problema planteado y los beneficios esperados.')
    ]),
    dcc.Tab(label='5. Marco Teórico', children=[
        html.H2('Marco Teórico'),
        html.P('Resumen de conceptos teóricos (definiciones formales) claves relacionados con el proyecto. Se pueden incluir referencias o citas.')
    ]),
    dcc.Tab(label='6. Metodología', children=[
        html.H2('Metodología'),
        subtabs_metodologia
    ]),
    dcc.Tab(label='7. Resultados y Análisis Final', children=[
        html.H2('Resultados y Análisis Final'),
        subtabs_resultados
    ]),
    dcc.Tab(label='8. Conclusiones', children=[
        html.H2('Conclusiones'),
        html.Ul([
            html.Li('Listar los principales hallazgos del proyecto'),
            html.Li('Relevancia de los resultados obtenidos'),
            html.Li('Aplicaciones futuras y recomendaciones')
        ])
    ])
]


app.layout = dbc.Container(
    [
        html.H1("Dashboard del Proyecto Final", className="text-center my-4"),

        # ⬇️ NUEVO: muestra TODAS las pestañas de primer nivel correctamente
        dcc.Tabs(children=tabs)
    ],
    fluid=True
)



@app.callback(
    [
        # Líneas
        Output("line-ban",             "figure"),
        Output("line-hist",            "figure"),
        Output("line-hist-ciudad",     "figure"),
        # Barras de nulos
        Output("bar-nulos-ban",        "figure"),
        Output("bar-nulos-hist",       "figure"),
        Output("bar-nulos-hist-ciudad","figure"),
        # Indicadores
        Output("count-ban",            "children"),
        Output("count-hist",           "children"),
        Output("count-hist-ciudad",    "children"),
    ],
    [  # Entradas
        Input("ciudad-ban",        "value"),
        Input("ciudad-hist",       "value"),
        Input("ciudad-hist-ciudad","value"),
    ],
)
def actualizar_panel(ciudad_ban, ciudad_hist_base, ciudad_hist_ciudad):

  
    ban_clean  = ban.copy()
    hist_clean = hist.copy()

    # >>> 1)  INDICADORES -------------------------------------------------
    def indicador(df):
        tot   = len(df)
        nulos = df["RADIACION"].isna().sum()
        return f"{tot:,} registros | {nulos / tot * 100:,.1f}% nulos"

 
    df_b = ban_clean[ban_clean["CIUDAD"] == ciudad_ban]
    indicador_b = indicador(df_b)

    
    hist_clean["BASE"] = hist_clean["CIUDAD"].str.extract(r"^([A-Z\s]+)")[0].str.strip()
    df_h_base = hist_clean[hist_clean["BASE"] == ciudad_hist_base]
    indicador_h = indicador(df_h_base)

   
    df_h_ciudad = hist_clean[hist_clean["CIUDAD"] == ciudad_hist_ciudad]
    indicador_h_ciudad = indicador(df_h_ciudad)

    # >>> 2)  GRÁFICOS DE LÍNEAS ------------------------------------------
    fig_ban = px.line(df_b.sort_values("FECHA_HORA"),
                      x="FECHA_HORA", y="RADIACION",
                      title=f"Radiación BAN – {ciudad_ban}")\
                .update_traces(mode="lines", showlegend=False)

    fig_hist = px.line(df_h_base.sort_values("FECHA_HORA"),
                       x="FECHA_HORA", y="RADIACION", color="CIUDAD",
                       title=f"Radiación HIST – {ciudad_hist_base}")\
                .update_traces(mode="lines")

    fig_hist_ciudad = px.line(df_h_ciudad.sort_values("FECHA_HORA"),
                              x="FECHA_HORA", y="RADIACION", color="CIUDAD",
                              title=f"Radiación HIST (estación) – {ciudad_hist_ciudad}")\
                       .update_traces(mode="lines")

    # >>> 3)  BARRAS DE % NULOS  (cálculo por grupo propio) ---------------
    # BAN  – por ciudad
    df_nulos_ban = (
       ban_clean.groupby("CIUDAD", group_keys=False)["RADIACION"]\
       .apply(lambda s: s.isna().mean() * 100)
       .reset_index(name="% nulos")
       .sort_values("% nulos", ascending=False)
    )
    fig_bar_ban = px.bar(df_nulos_ban, x="% nulos", y="CIUDAD",
                         orientation="h", color="% nulos",
                         color_continuous_scale="Reds",
                         title="% de valores nulos por ciudad (BAN)")\
                   .update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

    # HIST  – por base (sin altitud)
    df_nulos_hist_base = (
           hist_clean.groupby("BASE", group_keys=False)["RADIACION"]\
           .apply(lambda s: s.isna().mean() * 100)
           .reset_index(name="% nulos")
           .sort_values("% nulos", ascending=False)
    )
    fig_bar_hist = px.bar(df_nulos_hist_base, x="% nulos", y="BASE",
                          orientation="h", color="% nulos",
                          color_continuous_scale="Reds",
                          title="% de valores nulos por ciudad base (HIST)")\
                    .update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

   
    df_nulos_hist_ciudad = (
           hist_clean.groupby("CIUDAD", group_keys=False)["RADIACION"]\
           .apply(lambda s: s.isna().mean() * 100)
           .reset_index(name="% nulos")
           .sort_values("% nulos", ascending=False)
    )
    fig_bar_hist_ciudad = px.bar(df_nulos_hist_ciudad, x="% nulos", y="CIUDAD",
                                 orientation="h", color="% nulos",
                                 color_continuous_scale="Reds",
                                 title="% de valores nulos por estación completa (HIST)")\
                           .update_layout(yaxis_title="", xaxis_title="Porcentaje (%)")

   
    return (
        fig_ban, fig_hist, fig_hist_ciudad,
        fig_bar_ban, fig_bar_hist, fig_bar_hist_ciudad,
        indicador_b, indicador_h, indicador_h_ciudad
    )
    
    

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=False, host="0.0.0.0", port=port)
