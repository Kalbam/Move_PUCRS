
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

import pandas as pd
import numpy as np
import os
import json

from sqlalchemy import create_engine
from flask import send_from_directory

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Inicialización de la app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Forecasting Solar Radiation Using a Stacked Wavelet Transform-Based Machine Learning Model"
server = app.server



@server.route("/figures/<path:image_name>")
def serve_image(image_name):
    return send_from_directory(os.path.join(os.getcwd(), "figures"), image_name)

# Conexión a PostgreSQL 
# db_user = os.getenv("POSTGRES_USER", "postgres")
# db_pass = os.getenv("POSTGRES_PASSWORD", "KeylaAlba572")
# db_host = os.getenv("POSTGRES_HOST", "db")  
# db_port = os.getenv("POSTGRES_PORT", "5432")
# db_name = os.getenv("POSTGRES_DB", "radiation_inmet")
# Conexión a PostgreSQL render
# db_user = os.environ["POSTGRES_USER"]
# db_pass = os.environ["POSTGRES_PASSWORD"]
# db_host = os.environ["POSTGRES_HOST"]
# db_port = os.environ["POSTGRES_PORT"]
# db_name = os.environ["POSTGRES_DB"]

# engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")
# db_user = "radiation_inmet_db_v1_user"
# db_password = "5EshSNxUVp7iJIEX8ZLFA7miiGgcQeOJ"
# db_host = "dpg-d1d2ptqdbo4c73cb2j00-a.oregon-postgres.render.com"
# db_port = "5432"
# db_name = "radiation_inmet_db_v1"

#  Conexión segura con SSL
db_url = "postgresql://radiation_inmet_db_v1_user:5EshSNxUVp7iJIEX8ZLFA7miiGgcQeOJ@dpg-d1d2ptqdbo4c73cb2j00-a:5432/radiation_inmet_db_v1"

# Crear el engine
engine = create_engine(db_url)

ban = pd.read_sql("SELECT * FROM df_ban_inmet", engine)
hist = pd.read_sql("SELECT * FROM df_hist_inmet", engine)

# Limpieza y estandarización
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

estados_brasil = [
    'Acre', 'Alagoas', 'Amazonas', 'Amapá', 'Bahia', 'Ceará', 'Espírito Santo', 'Goiás',
    'Maranhão', 'Minas Gerais', 'Mato Grosso do Sul', 'Mato Grosso', 'Pará', 'Paraíba',
    'Pernambuco', 'Piauí', 'Paraná', 'Rio de Janeiro', 'Rio Grande do Norte',
    'Rondônia', 'Roraima', 'Rio Grande do Sul', 'Santa Catarina', 'Sergipe', 'São Paulo',
    'Tocantins', 'Distrito Federal'
]

estados_nordeste = [
    'Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba',
    'Pernambuco', 'Piauí', 'Rio Grande do Norte', 'Sergipe'
]




# with open("brazil-states.geojson", "r", encoding="utf-8") as f:
#     geojson_brasil = json.load(f) #local
geojson_path = os.path.join("figures", "brazil-states.geojson")

with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_brasil = json.load(f) #render

df_estados = pd.DataFrame({
    'Estado': estados_brasil,
    'Região': ['Nordeste' if estado in estados_nordeste else 'Outros' for estado in estados_brasil]
})

df_destacado = pd.DataFrame({
    'Estado': [estado for estado in estados_nordeste],
    'Grupo': ['São Luís' if estado == 'São Luís' else 'Outro Nordeste' for estado in estados_nordeste]
})

capitais = pd.DataFrame({
    'Cidade': ['Maceió', 'Salvador', 'Fortaleza', 'São Luís', 'João Pessoa',
               'Recife', 'Teresina', 'Natal', 'Aracaju'],
    'Lat': [-9.6658, -12.9714, -3.7319, -2.5307, -7.1153,
            -8.0476, -5.0892, -5.7945, -10.9472],
    'Lon': [-35.7350, -38.5014, -38.5267, -44.3028, -34.8631,
            -34.8770, -42.8016, -35.2110, -37.0731]
})


fig1 = px.choropleth(
    df_estados,
    geojson=geojson_brasil,
    locations="Estado",
    featureidkey="properties.name",
    color="Região",
    color_discrete_map={'Nordeste': 'salmon', 'Outros': 'lightgray'},
    labels={'Região': 'Região'}
)

fig2 = px.choropleth(
    df_destacado,
    geojson=geojson_brasil,
    locations="Estado",
    featureidkey="properties.name",
    color="Grupo",
    color_discrete_map={'Paraíba': 'orange', 'Outro Nordeste': 'salmon'},
    labels={'Grupo': 'Grupo'}
)

fig2.add_trace(go.Scattergeo(
    lon=capitais["Lon"],
    lat=capitais["Lat"],
    text=capitais["Cidade"],
    mode='markers+text',
    marker=dict(size=12, symbol='triangle-up', color='black'),
    textposition="top center",
    name='Cidade'
))

fig_combined = make_subplots(
    rows=1, cols=2,
    subplot_titles=("Brasil com Região Nordeste", "Capitais do Nordeste"),
    specs=[[{"type": "choropleth"}, {"type": "choropleth"}]]
)

for trace in fig1.data:
    fig_combined.add_trace(trace, row=1, col=1)
for trace in fig2.data:
    fig_combined.add_trace(trace, row=1, col=2)

fig_combined.update_layout(
    height=700,
    width=1300,
    showlegend=True,
    font=dict(family="Arial", size=16),
    geo=dict(
        projection_type='mercator',
        center={"lat": -14.5, "lon": -52},
        fitbounds="locations",
        visible=False
    ),
    geo2=dict(
        projection_type='mercator',
        center={"lat": -9, "lon": -38.5},
        lonaxis=dict(range=[-50, -30]),
        lataxis=dict(range=[-20, 5]),
        visible=False
    )
)



# Subpestañas de metodología
subtabs_metodologia = dcc.Tabs([
    dcc.Tab(label='a. Model Definition', children=[
        html.Img(src="/figures/ecuaciones.png", style={
            "width": "60%",
            "marginTop": "20px",
            "border": "1px solid #ccc",
            "display": "block",
            "marginLeft": "auto",
            "marginRight": "auto"
        })
     
    ]),
    dcc.Tab(label='b. Técnica', children=[
        html.Img(src="/figures/staking.png", style={
            "width": "50%",
            "marginTop": "20px",
            "border": "1px solid #ccc",
            "display": "block",
            "marginLeft": "auto",
            "marginRight": "auto"
        })
     
    ]),
    dcc.Tab(label='c. Data Preparation', children=[
        html.Img(src="/figures/data.png", style={
            "width": "90%",
            "marginTop": "20px",
            "border": "1px solid #ccc",
            "display": "block",
            "marginLeft": "auto",
            "marginRight": "auto"
        })
    ]),

    dcc.Tab(label='d. Implementation', children=[
        html.Img(src="/figures/esquema_stacked.png", style={
            "width": "90%",
            "marginTop": "20px",
            "border": "1px solid #ccc",
            "display": "block",
            "marginLeft": "auto",
            "marginRight": "auto"
        })
    ]),

    dcc.Tab(label='e. Avaliação do Modelo', children=[
        html.Img(src="/figures/Errores.png", style={
            "width": "90%",
            "marginTop": "20px",
            "border": "1px solid #ccc",
            "display": "block",
            "marginLeft": "auto",
            "marginRight": "auto"
        })
        
    ])
])
# ──────────────────────────────────────────────────────────────────────
subtabs_resultados = dcc.Tabs(
    [
        dcc.Tab(
            label="a. EDA (Northeastern States)",
            children=[
                html.H4("a. Exploratory Analysis of Northeastern States of Brazil"),

                # ───────── Indicadores ─────────
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardHeader([
                            "Total Records from BANCO Data Source by City",
                                       html.A("Link", href="https://bdmep.inmet.gov.br/", target="_blank", style={"color": "white", "marginLeft": "10px"})]),
                        dbc.CardBody(html.H4(id="count-ban", className="card-title mb-0")),
                    ], color="primary", inverse=True), width=4),

                    dbc.Col(dbc.Card([
                        dbc.CardHeader([
                            "Total Records from Historical Data Source by City",
                        html.A("Link", href="https://portal.inmet.gov.br/dadoshistoricos", target="_blank", style={"color": "white", "marginLeft": "10px"})]),
                        dbc.CardBody(html.H4(id="count-hist", className="card-title mb-0")),
                    ], color="info", inverse=True), width=4),
                        

                    dbc.Col(dbc.Card([
                        dbc.CardHeader("Total Records from Historical Data Source by City and Altitude"),
                        dbc.CardBody(html.H4(id="count-hist-ciudad", className="card-title mb-0")),
                    ], color="danger", inverse=True), width=4),
                ], className="mb-4"),

                # ───────── Filtros ─────────
                dbc.Row([
                    # BAN
                    dbc.Col([
                        html.Label("City (df_ban_inmet)"),
                        dcc.Dropdown(
                            id="ciudad-ban",
                            options=[{"label": c, "value": c} for c in sorted(ban["CIUDAD"].unique())],
                            value=sorted(ban["CIUDAD"].unique())[0],
                            clearable=False,
                        ),
                    ], width=4),

                    # HIST agrupado por BASE (sin altitud)
                    dbc.Col([
                        html.Label("City (df_hist_inmet, agrupado)"),
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
                        html.Label("City(df_hist_inmet, con altitud)"),
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
                        html.H5("Evolution of Solar Radiation (Data Bank source) by city"),
                        dcc.Graph(id="line-ban"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("Evolution of Solar Radiation (Historical Data source) by city"),
                        dcc.Graph(id="line-hist"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("Evolution of Solar Radiation by city and altitude (Historical Data source)"),
                        dcc.Graph(id="line-hist-ciudad"),
                    ], lg=4, width=12),
                ]),

                html.Hr(),

                # ───────── Gráficos de barras ─────────
                html.H4("Percentage of Missing Values Chart", className="my-4 text-center"),
                dbc.Row([
                    dbc.Col([
                        html.H5("Missing Values (%) by City (Banco de Dados)", className="text-center"),
                        dcc.Graph(id="bar-nulos-ban"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("Missing Values (%) by City (Historical Source)", className="text-center"),
                        dcc.Graph(id="bar-nulos-hist"),
                    ], lg=4, width=12),

                    dbc.Col([
                        html.H5("Missing Values (%) by City & Altitude (Historical Data)", className="text-center"),
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

dcc.Tab(
    label='0. Cover Page',
    style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    },
    children=[
        html.Div(style={'textAlign': 'center', 'marginTop': '40px'}, children=[

            # Logos (CAPES, PUCRS, UN)
            html.Div([
                html.Img(src='/figures/logo_CAPES.png', style={'height': '120px', 'margin': '0 25px'}),
                html.Img(src='/figures/logo_PUCRS.png', style={'height': '120px', 'margin': '0 25px'}),
                html.Img(src='/figures/logo_UN.png', style={'height': '120px', 'margin': '0 25px'}),
            ], style={'display': 'flex', 'justifyContent': 'center'}),

            html.H1("Doctoral Research Stay", style={
                'color': '#004080',
                'marginTop': '40px',
                'fontWeight': 'bold'
            }),

            html.H3("Collaboration between:", style={'marginTop': '20px'}),

            html.H4("Center for Artificial Intelligence and Data Science – PUCRS"),
            html.H4("PhD in Computer Science – PUCRS"),
            html.H4("Pontifícia Universidade Católica do Rio Grande do Sul (PUCRS)"),
            html.H4("Universidad del Norte – PhD in Natural Sciences"),

            html.P("Funded by MOVE La América (CAPES Program)",
                   style={'fontStyle': 'italic', 'marginTop': '20px'}),

            html.P("Location: Porto Alegre, Rio Grande do Sul, Brazil"),

            html.H4("Researcher: Keyla Vanessa Alba Molina", style={'marginTop': '30px', 'fontWeight': 'bold'}),

            html.H5("Dr. Dalvan Griebler (PUCRS – Computer Science PhD Program)", style={
                'fontWeight': 'bold',
                'fontSize': '18px'
            }),
            html.H5("Dr. Lihki Rubio Ortega (Universidad del Norte – Natural Sciences PhD Program)", style={
                'fontWeight': 'bold',
                'fontSize': '18px'
            }),
        ])
    ]
),
    dcc.Tab(
    label='1. Introduction',
    style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    },
    children=[
        html.H2("Introduction", style={
            'textAlign': 'center',
            'marginTop': '20px',
            'marginBottom': '30px',
            'fontWeight': 'bold',
            'fontSize': '30px'
        }),

        # Paragraph Box
        html.Div(style={
            'backgroundColor': '#f9f9f9',
            'padding': '30px',
            'borderRadius': '10px',
            'border': '1px solid #ddd',
            'margin': '0 50px 40px',
            'fontSize': '120%',
            'lineHeight': '1.9',
            'textAlign': 'justify',
            'fontWeight': '500'
        }, children=[
            html.P(
                "Electrical systems constitute fundamental pillars for the economic and social development of any nation, "
                "as they enable access to essential services, drive productivity, and promote territorial equity "
                "(Bisaga et al., 2021; Garces et al., 2021). "
                "In this context, the transition toward renewable energy sources has gained increasing relevance, "
                "positioning solar energy as a strategic alternative due to its availability, sustainability, and cost reduction potential. "
                "As its implementation becomes more accessible both technologically and economically, the accuracy in solar radiation forecasting "
                "emerges as a critical input to maximize the efficiency and feasibility of photovoltaic systems "
                "(Hassan et al., 2023; Obaideen et al., 2023). "
                "Reliable estimations not only enhance energy planning but also allow for improved supply and demand management, "
                "particularly in territories characterized by high irradiation and low levels of electrification."
            )
        ]),

        # Image Cards
        html.Div(style={
            'display': 'flex',
            'justifyContent': 'space-evenly',
            'flexWrap': 'wrap',
            'gap': '30px',
            'paddingBottom': '40px'
        }, children=[

            # Card 1
            html.Div(style={
                'width': '500px',
                'textAlign': 'center',
                'border': '1px solid #ddd',
                'borderRadius': '10px',
                'padding': '18px',
                'backgroundColor': '#ffffff',
                'boxShadow': '2px 2px 6px rgba(0,0,0,0.1)'
            }, children=[
                html.Img(src='/figures/Sistemas_electricos.png',
                         style={'width': '60%', 'height': 'auto'}),
                html.P([html.Strong('Figure 1. '), 'Illustration of electrical systems'],
                       style={'fontSize': '115%', 'fontWeight': 'bold'}),
                html.P('Source: Customized institutional image',
                       style={'fontSize': '105%', 'fontStyle': 'italic'})
            ]),

            # Card 2
            html.Div(style={
                'width': '500px',
                'textAlign': 'center',
                'border': '1px solid #ddd',
                'borderRadius': '10px',
                'padding': '18px',
                'backgroundColor': '#ffffff',
                'boxShadow': '2px 2px 6px rgba(0,0,0,0.1)'
            }, children=[
                html.Img(src='/figures/Mapa_Br_Rad.png',
                         style={'width': '60%', 'height': 'auto'}),
                html.P([html.Strong('Figure 2. '), 'Solar Irradiation Map'],
                       style={'fontSize': '115%', 'fontWeight': 'bold'}),
                html.P('Source: Brazil Solar Atlas, 2020',
                       style={'fontSize': '105%', 'fontStyle': 'italic'})
            ]),

            # Card 3
            html.Div(style={
                'width': '500px',
                'textAlign': 'center',
                'border': '1px solid #ddd',
                'borderRadius': '10px',
                'padding': '18px',
                'backgroundColor': '#ffffff',
                'boxShadow': '2px 2px 6px rgba(0,0,0,0.1)'
            }, children=[
                html.Img(src='/figures/Mapa_Br_PHV.png',
                         style={'width': '60%', 'height': 'auto'}),
                html.P([html.Strong('Figure 3. '), 'Photovoltaic Potential Map'],
                       style={'fontSize': '115%', 'fontWeight': 'bold'}),
                html.P('Source: Brazil Solar Atlas, 2020',
                       style={'fontSize': '105%', 'fontStyle': 'italic'})
            ])
        ])
    ]
),

    # Pestaña 2 - Contexto
dcc.Tab(
    label='2. Context',
    style={
        'fontWeight': 'bold', 'fontSize': '18px',
        'backgroundColor': '#f2f2f2', 'color': '#004080', 'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold', 'fontSize': '18px',
        'backgroundColor': '#004080', 'color': 'white', 'padding': '12px',
        'borderBottom': '4px solid orange'
    },
    children=[
        html.H2('Northeastern States of Brazil',
                style={'textAlign': 'center', 'marginBottom': '40px'}),

        html.Div(style={'display': 'flex', 'flexDirection': 'row'}, children=[

            # -------- LEFT COLUMN · TEXT INDICATORS --------
            html.Div(style={
                'width': '40%', 'padding': '0 20px',
                'fontSize': '110%', 'lineHeight': '1.7'
            }, children=[

                # Indicator 1
                html.Div(style={
                    'backgroundColor': '#f8f9fa', 'border': '1px solid #ccc',
                    'borderRadius': '10px', 'padding': '20px', 'marginBottom': '20px'
                }, children=[
                    html.B(
                        "Northeastern Brazil presents exceptional climatic conditions for solar energy generation, "
                        "with some of the highest levels of solar irradiation in the country. "
                        "This region is a priority for the analysis of global solar radiation as measured by INMET."
                    )
                ]),

                # Indicator 2
                html.Div(style={
                    'backgroundColor': '#f8f9fa', 'border': '1px solid #ccc',
                    'borderRadius': '10px', 'padding': '20px', 'marginBottom': '20px'
                }, children=[
                    html.B(
                        "Global solar radiation includes both direct and diffuse radiation received on a horizontal surface. "
                        "This metric is essential to evaluate the photovoltaic potential of a region."
                    )
                ]),

                # Indicator 3 · Metadata
                html.Div(style={
                    'backgroundColor': '#f8f9fa', 'border': '1px solid #ccc',
                    'borderRadius': '10px', 'padding': '20px'
                }, children=[
                    html.P([html.Strong("Source: "), "INMET"], style={'fontSize': '135%'}),
                    html.P([html.Strong("Link: "),
                            html.A("https://portal.inmet.gov.br/",
                                   href="https://portal.inmet.gov.br/",
                                   target="_blank")], style={'fontSize': '135%'}),
                    html.P([html.Strong("Period: "), "2000–2025 (30-04)"], style={'fontSize': '135%'}),
                    html.P([html.Strong("Variable of interest: "),
                            "Global Solar Radiation (W/m²)"], style={'fontSize': '135%'})
                ])
            ]),

            # -------- RIGHT COLUMN · COMBINED MAP --------
            html.Div(style={'width': '60%', 'padding': '0 20px'}, children=[
                dcc.Graph(figure=fig_combined,
                          config={'displayModeBar': False},
                          style={'height': '650px'})
            ])
        ])
    ]
),

    # dcc.Tab(label='3. Background',style={
    #     'fontWeight': 'bold',
    #     'fontSize': '18px',
    #     'backgroundColor': '#f2f2f2',
    #     'color': '#004080',
    #     'padding': '12px'
    # },
    # selected_style={
    #     'fontWeight': 'bold',
    #     'fontSize': '18px',
    #     'backgroundColor': '#004080',
    #     'color': 'white',
    #     'padding': '12px',
    #     'borderBottom': '4px solid orange'
    # }, children=[

    # ]),
    
dcc.Tab(
    label='3. Background',
    style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    },
    children=[
        html.H2("Evolution of Ensemble Models", style={'textAlign': 'center'}),

        # ───────────────────────── 1st ROW 2015–2019 ─────────────────────────
        html.Div(style={
            'position': 'relative',
            'padding': '50px 10px 70px',
            'display': 'flex',
            'justifyContent': 'space-around',
            'alignItems': 'flex-start',
            'flexWrap': 'nowrap',
            'borderTop': '4px solid #ccc'
        }, children=[
            html.Div(style={
                'position': 'absolute',
                'top': '170px',
                'left': 0,
                'right': 0,
                'height': '4px',
                'backgroundColor': '#003366',
                'zIndex': 0
            }),

            *[
                html.Div(style={'width': '220px', 'textAlign': 'center', 'zIndex': 1}, children=[
                    html.Div(style={
                        'background': '#f0f8ff',
                        'padding': '15px',
                        'height': '140px',
                        'borderLeft': '5px solid #003366',
                        'borderRadius': '8px'
                    }, children=[
                        html.Strong(year, style={'fontSize': '20px'}),
                        html.Br(),
                        html.B(author), html.Br(),
                        html.Em(description)
                    ]),
                    html.Div(style={
                        'width': '14px', 'height': '14px',
                        'background': '#003366', 'borderRadius': '50%',
                        'margin': '10px auto'
                    })
                ]) for year, author, description in [
                    ("2015", "Olatomiwa et al.",
                     "SVM + Firefly for\nsolar radiation forecasting."),
                    ("2016", "Wang et al.",
                     "Comparison of hybrid\nmodels for solar radiation."),
                    ("2017", "Voyant et al.",
                     "Review of machine learning\ntechniques for radiation."),
                    ("2018", "Sobri et al.",
                     "Review of photovoltaic\nforecasting methods."),
                    ("2019", "Benali et al.",
                     "Solar forecasting using\nANN and Random Forest.")
                ]
            ]
        ]),

        # ───────────────────────── 2nd ROW 2020–2024 ─────────────────────────
        html.Div(style={
            'position': 'relative',
            'padding': '50px 10px 70px',
            'display': 'flex',
            'justifyContent': 'space-around',
            'alignItems': 'flex-start',
            'flexWrap': 'nowrap',
            'borderTop': '4px solid #ccc'
        }, children=[
            html.Div(style={
                'position': 'absolute',
                'top': '170px',
                'left': 0,
                'right': 0,
                'height': '4px',
                'backgroundColor': '#003366',
                'zIndex': 0
            }),

            *[
                html.Div(style={'width': '220px', 'textAlign': 'center', 'zIndex': 1}, children=[
                    html.Div(style={
                        'background': '#f0f8ff',
                        'padding': '15px',
                        'height': '140px',
                        'borderLeft': '5px solid #003366',
                        'borderRadius': '8px'
                    }, children=[
                        html.Strong(year, style={'fontSize': '20px'}),
                        html.Br(),
                        html.B(author), html.Br(),
                        html.Em(description)
                    ]),
                    html.Div(style={
                        'width': '14px', 'height': '14px',
                        'background': '#003366', 'borderRadius': '50%',
                        'margin': '10px auto'
                    })
                ]) for year, author, description in [
                    ("2020", "Gao et al.",
                     "Hourly forecasting using\nCEEMDAN + CNN-LSTM."),
                    ("2021", "Kumari et al.",
                     "Hybrid LSTM-CNN model\nfor solar irradiance."),
                    ("2022", "Wei et al.",
                     "Spatiotemporal mapping\nwith pollution as a variable."),
                    ("2023", "Gaboitaolelwe et al.",
                     "Comparison of ML models\nfor photovoltaic energy."),
                    ("2024", "Gao et al.",
                     "Transfer learning with ADDA\nfor solar prediction.")
                ]
            ]
        ])
    ]
),
    

    dcc.Tab(
    label='4. Problem',
    style={
        'fontWeight': 'bold', 'fontSize': '18px',
        'backgroundColor': '#f2f2f2', 'color': '#004080', 'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold', 'fontSize': '18px',
        'backgroundColor': '#004080', 'color': 'white', 'padding': '12px',
        'borderBottom': '4px solid orange'
    },
    children=[
        html.H2('Problem Statement', style={'textAlign': 'center'}),

        # --- INDICATORS ---
        html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px'}, children=[

            html.Div(style={
                'border': '1px solid #ccc', 'borderRadius': '10px',
                'padding': '20px', 'width': '32%', 'backgroundColor': '#fdecea',
                'boxShadow': '2px 2px 6px rgba(0,0,0,0.1)'
            }, children=[
                html.Div("Global Fossil Fuel Dependency", style={
                    'fontWeight': 'bold','fontSize': '18px', 'backgroundColor': '#f8d7da',
                    'padding': '6px', 'borderRadius': '5px', 'textAlign': 'center'
                }),
                html.H4("85% in 2023", style={'color': 'darkred', 'marginTop': '15px', 'textAlign': 'center'}),
                html.P("Most of the world's energy still comes from fossil sources.", style={'textAlign': 'justify'}),
                html.P(html.B(" Benali et al., 2019"), style={'fontSize': '100%', 'color': '#555', 'textAlign': 'right'})
            ]),

            html.Div(style={
                'border': '1px solid #ccc', 'borderRadius': '10px',
                'padding': '20px', 'width': '32%', 'backgroundColor': '#eafaf1',
                'boxShadow': '2px 2px 6px rgba(0,0,0,0.1)'
            }, children=[
                html.Div("Brazil's Progress in Renewables", style={
                    'fontWeight': 'bold','fontSize': '18px', 'backgroundColor': '#d4edda',
                    'padding': '6px', 'borderRadius': '5px', 'textAlign': 'center'
                }),
                html.H4("83.79% renewable", style={'color': 'green', 'marginTop': '15px', 'textAlign': 'center'}),
                html.P("Brazil leads Latin America in energy transition.", style={'textAlign': 'justify'}),
                html.P(html.B("Sobri et al., 2018"), style={'fontSize': '100%', 'color': '#555', 'textAlign': 'right'})
            ]),

            html.Div(style={
                'border': '1px solid #ccc', 'borderRadius': '10px',
                'padding': '20px', 'width': '32%', 'fontSize': '18px','backgroundColor': '#fff9db',
                'boxShadow': '2px 2px 6px rgba(0,0,0,0.1)'
            }, children=[
                html.Div("High Density of Solar Projects", style={
                    'fontWeight': 'bold', 'backgroundColor': '#fff3cd',
                    'padding': '6px', 'borderRadius': '5px', 'textAlign': 'center'
                }),
                html.H4("Northeast Brazil", style={'color': '#c28700', 'marginTop': '15px', 'textAlign': 'center'}),
                html.P("Key area for solar energy planning.", style={'textAlign': 'justify'}),
                html.P(html.B(" Wei et al., 2022"), style={'fontSize': '100%', 'color': '#555', 'textAlign': 'right'})
            ])
        ]),

        # --- MAPA ILUSTRATIVO ---
        html.Div(style={'textAlign': 'center', 'marginBottom': '30px'}, children=[
            html.Img(src='/figures/Matriz_Br.png', style={
                'width': '75%', 'border': '1px solid #ccc', 'borderRadius': '8px'
            }),
            html.P([html.Strong('Figure 5. '),
                'Map of energy projects and transmission lines in Brazil'],
                style={'fontSize': '110%', 'marginTop': '10px'}
            ),
            html.P(html.B('Source: Agência Nacional de Energia Elétrica (ANEEL)'),
                   style={'fontSize': '110%', 'fontStyle': 'italic'})
        ]),

        # --- RESEARCH QUESTION ---
        html.Div(style={
            'border': '2px solid #003366',
            'borderRadius': '12px',
            'padding': '30px',
            'margin': '0 auto 40px',
            'maxWidth': '90%',
            'backgroundColor': '#f0f8ff',
            'boxShadow': '2px 2px 10px rgba(0,0,0,0.1)'
        }, children=[
            html.H3("Research Question", style={
                'textAlign': 'center',
                'color': '#003366',
                'fontWeight': 'bold',
                'fontSize': '34px'
            }),
            html.B(
                "Can a hybrid strategy based on DWT, individual models, and XGBoost stacking, optimized with Optuna, accurately forecast solar radiation to support renewable energy planning?",
                style={'fontSize': '160%', 'textAlign': 'justify', 'lineHeight': '1.8'}
            )
        ])
    ]
),
dcc.Tab(
    label='5. Objectives & Legal',
    style={'fontWeight': 'bold', 'fontSize': '18px',
           'backgroundColor': '#f2f2f2', 'color': '#004080', 'padding': '12px'},
    selected_style={'fontWeight': 'bold', 'fontSize': '22px',
                    'backgroundColor': '#004080', 'color': 'white',
                    'padding': '12px', 'borderBottom': '4px solid orange'},
    children=[
        html.H2("Objectives and Legal Framework", style={
            'textAlign': 'center', 'marginBottom': '40px', 'fontWeight': 'bold'
        }),

        html.Div(style={
            'display': 'flex', 'flexWrap': 'wrap',
            'justifyContent': 'space-between', 'gap': '40px',
            'padding': '0 40px'
        }, children=[

            # -------- OBJECTIVES (izq.) --------
            html.Div(style={
                'flex': '1', 'minWidth': '420px',
                'backgroundColor': '#f9f9f9',
                'padding': '30px', 'borderRadius': '10px',
                'border': '1px solid #ccc',
                'fontSize': '135%', 'lineHeight': '1.8'
            }, children=[
                html.H3("General Objective", style={'color': '#003366', 'fontWeight': 'bold'}),
                html.P([
                    "To forecast solar radiation using a multiscale hybrid model that integrates ",
                    html.B("Discrete Wavelet Transform (DWT)"),
                    " decomposition, individual predictors (",
                    html.B("ARIMA, ETS, Prophet, SVR, MLP, LSTM, RNN"),
                    ") and stacked ensembling with ",
                    html.B("XGBoost"),
                    ", optimized via ",
                    html.B("Optuna"),
                    "."
                ]),

                html.H3("Specific Objectives", style={
                    'color': '#003366', 'fontWeight': 'bold', 'marginTop': '30px'
                }),
                html.Ul([
                    html.Li([
                        "Conduct an ", html.B("Exploratory Data Analysis (EDA)"),
                        " of solar-radiation time series from Brazil’s Northeast (INMET)."
                    ]),
                    html.Li([
                        "Forecast low- and high-frequency ", html.B("DWT"),
                        " components with ", html.B("Optuna-tuned models (ARIMA, SVR, MLP, LSTM, RNN)"),
                        " stacked via ", html.B("XGBoost"), "."
                    ]),
                    html.Li([
                        "Reconstruct the original signal via inverse ", html.B("DWT"),
                        " and evaluate the ",
                        html.B("DWT–Stacked–XGBoost"), " model with ",
                        html.B("RMSE, MAE, MAPE, R²"), " under ",
                        html.B("Group K-Fold"), "."
                    ])
                ])
            ]),

            # -------- LEGAL (der.) --------
            html.Div(style={
                'flex': '1', 'minWidth': '420px',
                'display': 'flex', 'flexDirection': 'column',
                'gap': '30px'
            }, children=[

                # International
                html.Div(style={
                    'backgroundColor': '#f0f8ff',
                    'padding': '25px', 'borderRadius': '15px',
                    'border': '3px solid #3399ff','fontSize': '22px',
                    'boxShadow': '3px 3px 10px rgba(0,0,0,0.08)',
                    'textAlign': 'center'
                }, children=[
                    html.Img(src='/figures/internacional.png', style={'width': '120px', 'marginBottom': '15px'}),
                    html.H4("International Level", style={'color': '#003366', 'fontWeight': 'bold'}),
                    html.P([
                        html.B("IRENA: "),
                        "Promotes global adoption of renewable energies via regulatory frameworks and technical cooperation."
                    ], style={'textAlign': 'justify'}),
                    html.P([
                        html.B("UNEP: "),
                        "Encourages sustainable energy policies and programmes accelerating the transition to renewables."
                    ], style={'textAlign': 'justify'})
                ]),

                # National
                html.Div(style={
                    'backgroundColor': '#fffbe6',
                    'padding': '25px', 'borderRadius': '15px',
                    'border': '3px solid #ffcc00','fontSize': '22px',
                    'boxShadow': '3px 3px 10px rgba(0,0,0,0.08)',
                    'textAlign': 'center'
                }, children=[
                    html.Img(src='/figures/nacional.png', style={'width': '120px', 'marginBottom': '15px'}),
                    html.H4("National Level – Brazil", style={'color': '#663300', 'fontWeight': 'bold'}),
                    html.Ul(style={'textAlign': 'left', 'paddingLeft': '20px'}, children=[
                        html.Li([html.B("Law No. 14.300/2022: "),
                                 "Framework for distributed generation (tax benefits until 2045)."]),
                        html.Li([html.B("ANEEL Res. 482/2012: "),
                                 "Regulates the net-metering system."]),
                        html.Li([html.B("PROINFA: "),
                                 "Diversifies energy sources (solar, wind, biomass)."]),
                        html.Li([html.B("RenovaBio: "),
                                 "Sustainability programme with emission-reduction targets."]),
                        html.Li([html.B("PDE 2031: "),
                                 "Projects 83 % renewables with strong solar growth."])
                    ])
                ])
            ])
        ])
    ]
),
dcc.Tab(
    label='6. Justification',
    style={'fontWeight': 'bold', 'fontSize': '18px',
           'backgroundColor': '#f2f2f2', 'color': '#004080', 'padding': '12px'},
    selected_style={'fontWeight': 'bold', 'fontSize': '22px',
                    'backgroundColor': '#004080', 'color': 'white',
                    'padding': '12px', 'borderBottom': '4px solid orange'},
    children=[
        html.H2("Project Justification", style={
            'textAlign': 'center', 'marginBottom': '40px', 'fontWeight': 'bold'
        }),

        html.Div(style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))',
            'gap': '30px',
            'padding': '0 60px'
        }, children=[

            # TECHNOLOGY
            html.Div(style={
                'textAlign': 'center',
                'backgroundColor': '#f2f2f2',
                'border': '1px solid #ccc',
                'borderRadius': '15px',
                'padding': '25px','fontSize': '22px',
                'boxShadow': '2px 2px 8px rgba(0, 0, 0, 0.05)'
            }, children=[
                html.Img(src='/figures/tecnologia.png', style={'width': '160px', 'marginBottom': '20px'}),
                html.H4("Technology", style={'color': '#003366', 'fontWeight': 'bold', 'marginTop': '10px'}),
                html.P("The integration of wavelet decomposition and advanced learning algorithms provides robust, adaptable predictive tools. These allow for efficient planning and monitoring of photovoltaic systems in areas with limited historical data or infrastructure.")
            ]),

            # SCIENCE
            html.Div(style={
                'textAlign': 'center',
                'backgroundColor': '#f2f2f2',
                'border': '1px solid #ccc','fontSize': '22px',
                'borderRadius': '15px',
                'padding': '25px',
                'boxShadow': '2px 2px 8px rgba(0, 0, 0, 0.05)'
            }, children=[
                html.Img(src='/figures/ciencia.png', style={'width': '160px', 'marginBottom': '20px'}),
                html.H4("Science", style={'color': '#660033', 'fontWeight': 'bold', 'marginTop': '10px'}),
                html.P("This research contributes to the scientific field by exploring hybrid approaches combining Discrete Wavelet Transform (DWT) and machine learning models. It enhances understanding of nonlinear dynamics in solar radiation and time-series forecasting.")
            ]),

            # SOCIAL IMPACT
            html.Div(style={
                'textAlign': 'center',
                'backgroundColor': '#f2f2f2',
                'border': '1px solid #ccc','fontSize': '22px',
                'borderRadius': '15px',
                'padding': '25px',
                'boxShadow': '2px 2px 8px rgba(0, 0, 0, 0.05)'
            }, children=[
                html.Img(src='/figures/impacto_social.png', style={'width': '160px', 'marginBottom': '20px'}),
                html.H4("Social Impact", style={'color': '#006633', 'fontWeight': 'bold', 'marginTop': '10px'}),
                html.P("Reducing energy poverty and inequality, this project facilitates access to clean energy in marginalized regions. By enabling more reliable solar energy forecasting, it supports sustainable development goals and enhances quality of life.")
            ]),

            # ENVIRONMENTAL IMPACT
            html.Div(style={
                'textAlign': 'center',
                'backgroundColor': '#f2f2f2',
                'border': '1px solid #ccc',
                'borderRadius': '15px','fontSize': '22px',
                'padding': '25px',
                'boxShadow': '2px 2px 8px rgba(0, 0, 0, 0.05)'
            }, children=[
                html.Img(src='/figures/impacto_ambiental.png', style={'width': '160px', 'marginBottom': '20px'}),
                html.H4("Environmental Impact", style={'color': '#336600', 'fontWeight': 'bold', 'marginTop': '10px'}),
                html.P("By promoting greater integration of renewable energy, the project contributes to reducing reliance on fossil fuels, lowering greenhouse gas emissions, and supporting the transition to a cleaner, more resilient energy matrix.")
            ])
        ])
    ]
),
    dcc.Tab(label='7. Methodology',style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    }, children=[
        html.H2(''),
        subtabs_metodologia
    ]),
    dcc.Tab(label='8. Results and Final Analysis',style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    }, children=[
        html.H2(''),
        subtabs_resultados
    ]),
      dcc.Tab(label='9. Conclusions',style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    }, children=[
        html.H2(''),
        html.Ul([
            html.Li('Listar los principales hallazgos del proyecto'),
            html.Li('Relevancia de los resultados obtenidos'),
            html.Li('Aplicaciones futuras y recomendaciones')
            ])

    ]),
    dcc.Tab(label='10. References',style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#f2f2f2',
        'color': '#004080',
        'padding': '12px'
    },
    selected_style={
        'fontWeight': 'bold',
        'fontSize': '18px',
        'backgroundColor': '#004080',
        'color': 'white',
        'padding': '12px',
        'borderBottom': '4px solid orange'
    }, children=[
        html.H2(''),
        # html.Ul([
        #     html.Li('Listar los principales hallazgos del proyecto'),
        #     html.Li('Relevancia de los resultados obtenidos'),
        #     html.Li('Aplicaciones futuras y recomendaciones')
        # ])
    ])
]


app.layout = dbc.Container(
    [
        html.H1("Forecasting Solar Radiation Using a Stacked Wavelet Transform-Based Machine Learning Model", className="text-center my-4"),

        
        dcc.Tabs(children=tabs)
    ],
    fluid=True
)



# ═══════════════════════════════════════════════════════════════════════
# CALLBACK  • limpia, agrupa y dibuja
# ═══════════════════════════════════════════════════════════════════════

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

    # Los DataFrames ya están limpios y listos
    ban_clean  = ban.copy()
    hist_clean = hist.copy()

    # >>> 1)  INDICADORES -------------------------------------------------
    def indicador(df):
        tot   = len(df)
        Missing = df["RADIACION"].isna().sum()
        return f"{tot:,} Records | {Missing / tot * 100:,.1f}% Missing"

    # BAN seleccionado
    df_b = ban_clean[ban_clean["CIUDAD"] == ciudad_ban]
    indicador_b = indicador(df_b)

    # HIST por BASE (sin altitud)  ─ se extrae la base textual
    hist_clean["BASE"] = hist_clean["CIUDAD"].str.extract(r"^([A-Z\s]+)")[0].str.strip()
    df_h_base = hist_clean[hist_clean["BASE"] == ciudad_hist_base]
    indicador_h = indicador(df_h_base)

    # HIST por ciudad-estación (con altitud)
    df_h_ciudad = hist_clean[hist_clean["CIUDAD"] == ciudad_hist_ciudad]
    indicador_h_ciudad = indicador(df_h_ciudad)

    # >>> 2)  GRÁFICOS DE LÍNEAS ------------------------------------------
    fig_ban = px.line(df_b.sort_values("FECHA_HORA"),
                      x="FECHA_HORA", y="RADIACION",
                      title=f"City – {ciudad_ban}")\
                .update_traces(mode="lines", showlegend=False)

    fig_hist = px.line(df_h_base.sort_values("FECHA_HORA"),
                       x="FECHA_HORA", y="RADIACION", color="CIUDAD",
                       title=f"City – {ciudad_hist_base}")\
                .update_traces(mode="lines")

    fig_hist_ciudad = px.line(df_h_ciudad.sort_values("FECHA_HORA"),
                              x="FECHA_HORA", y="RADIACION", color="CIUDAD",
                              title=f"City – {ciudad_hist_ciudad}")\
                       .update_traces(mode="lines")

    # >>> 3)  BARRAS DE % NULOS  (cálculo por grupo propio) ---------------
    # BAN  – por ciudad
    df_nulos_ban = (
       ban_clean.groupby("CIUDAD", group_keys=False)["RADIACION"]\
       .apply(lambda s: s.isna().mean() * 100)
       .reset_index(name="% Missing")
       .sort_values("% Missing", ascending=False)
    )
    fig_bar_ban = px.bar(df_nulos_ban, x="% Missing", y="CIUDAD",
                         orientation="h", color="% Missing",
                         color_continuous_scale="Reds",
                         title="")\
                   .update_layout(yaxis_title="", xaxis_title="Percentage (%)")

    # HIST  – por base (sin altitud)
    df_nulos_hist_base = (
           hist_clean.groupby("BASE", group_keys=False)["RADIACION"]\
           .apply(lambda s: s.isna().mean() * 100)
           .reset_index(name="% Missing")
           .sort_values("% Missing", ascending=False)
    )
    fig_bar_hist = px.bar(df_nulos_hist_base, x="% Missing", y="BASE",
                          orientation="h", color="% Missing",
                          color_continuous_scale="Reds",
                          title="")\
                    .update_layout(yaxis_title="", xaxis_title="Percentage (%)")

    # HIST  – por ciudad-estación (con altitud)
    df_nulos_hist_ciudad = (
           hist_clean.groupby("CIUDAD", group_keys=False)["RADIACION"]\
           .apply(lambda s: s.isna().mean() * 100)
           .reset_index(name="% Missing")
           .sort_values("% Missing", ascending=False)
    )
    fig_bar_hist_ciudad = px.bar(df_nulos_hist_ciudad, x="% Missing", y="CIUDAD",
                                 orientation="h", color="% Missing",
                                 color_continuous_scale="Reds",
                                 title="")\
                           .update_layout(yaxis_title="", xaxis_title="Percentage (%)")

    # >>> 4)  Devolver todo al dashboard ----------------------------------
    return (
        fig_ban, fig_hist, fig_hist_ciudad,
        fig_bar_ban, fig_bar_hist, fig_bar_hist_ciudad,
        indicador_b, indicador_h, indicador_h_ciudad
    )
    
    
# Ejecutar la app
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8050))
#     app.run_server(debug=False, host="0.0.0.0", port=port)
#server = app.server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run_server(host="0.0.0.0", port=port)
