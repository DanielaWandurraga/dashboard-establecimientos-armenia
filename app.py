import os
import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import gdown

# ---------------------------------------------------------
# Carga de la base de datos
# ---------------------------------------------------------

ARCHIVO = "Establecimientos_de_Comercio_Activos_Armenia_20260903.csv"
DRIVE_ID = "1H5Um1uqZWeOIsoIXyYJl_6555xGnMH_o"

if not os.path.exists(ARCHIVO):
    gdown.download(
        id=DRIVE_ID,
        output=ARCHIVO,
        quiet=False
    )

df = pd.read_csv(ARCHIVO)

# ---------------------------------------------------------
# Preparación y normalización de los datos
# ---------------------------------------------------------

df_dash = df.copy()

df_dash["ANIO-DATOS-LIMPIO"] = np.where(
    df_dash["ANIO-DATOS"].between(2, 3),
    (df_dash["ANIO-DATOS"] * 1000).round().astype("Int64"),
    pd.NA
)

df_dash["ULT-ANO_REN-LIMPIO"] = np.where(
    df_dash["ULT-ANO_REN"].between(2, 3),
    (df_dash["ULT-ANO_REN"] * 1000).round().astype("Int64"),
    pd.NA
)

columnas_fecha = ["FEC-MATRICULA", "FEC-RENOVACION", "FECHA-DATOS"]
for columna in columnas_fecha:
    df_dash[columna + "-LIMPIA"] = pd.to_datetime(
        df_dash[columna].astype("string").str.replace(".", "", regex=False),
        format="%Y%m%d",
        errors="coerce"
    )

df_dash["MUN-COMERCIAL"] = (
    df_dash["MUN-COMERCIAL"].fillna("Sin información").astype(str).str.strip()
)
df_dash["ACTIVIDAD"] = (
    df_dash["ACTIVIDAD"].fillna("Sin información").astype(str).str.strip()
)

municipios = sorted(df_dash["MUN-COMERCIAL"].dropna().unique().tolist())
anios = sorted(df_dash["ANIO-DATOS-LIMPIO"].dropna().astype(int).unique().tolist())

# ---------------------------------------------------------
# Aplicación Dash
# ---------------------------------------------------------

app = Dash(__name__)

app.layout = html.Div([

    html.H1(
        "Dashboard de Establecimientos de Comercio Activos",
        style={
            "textAlign": "center",
            "marginBottom": "30px"
        }
    ),

    html.H3("Filtros de análisis"),

    # Selector de variable numérica
    html.Label("Variable numérica:"),
    dcc.Dropdown(
        id="selector-numerico",
        options=[
            {
                "label": "Año de los datos",
                "value": "ANIO-DATOS-LIMPIO"
            },
            {
                "label": "Año de última renovación",
                "value": "ULT-ANO_REN-LIMPIO"
            },
            {
                "label": "Año de matrícula",
                "value": "ANIO_MATRICULA"
            }
        ],
        value="ANIO-DATOS-LIMPIO",
        clearable=False
    ),

    html.Br(),

    # Selector de variable categórica
    html.Label("Variable categórica:"),
    dcc.Dropdown(
        id="selector-categorico",
        options=[
            {
                "label": "Municipio comercial",
                "value": "MUN-COMERCIAL"
            },
            {
                "label": "Actividad económica",
                "value": "ACTIVIDAD"
            }
        ],
        value="MUN-COMERCIAL",
        clearable=False
    ),

    html.Br(),

    # Filtro por año
    html.Label("Filtro por año:"),
    dcc.Dropdown(
        id="filtro-anio",
        options=[
            {"label": "Todos los años", "value": "todos"}
        ] + [
            {"label": str(anio), "value": anio}
            for anio in anios
        ],
        value="todos",
        clearable=False
    ),

    html.Br(),

    # Filtro por municipio
    html.Label("Filtro por municipio:"),
    dcc.Dropdown(
        id="filtro-municipio",
        options=[
            {"label": "Todos los municipios", "value": "todos"}
        ] + [
            {"label": municipio, "value": municipio}
            for municipio in municipios
        ],
        value="todos",
        clearable=False
    ),

    html.Hr(),

    # KPI
    html.Div(
        id="kpi",
        style={
            "fontSize": "28px",
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": "20px"
        }
    ),

    # Exploración dinámica
    html.H2("Exploración interactiva"),

    dcc.Graph(id="grafico-dinamico"),

    html.Hr(),

    # Gráficos univariados
    html.H2("Análisis univariado"),

    dcc.Graph(id="uni-1"),
    dcc.Graph(id="uni-2"),
    dcc.Graph(id="uni-3"),
    dcc.Graph(id="uni-4"),
    dcc.Graph(id="uni-5"),

    html.Hr(),

    # Gráficos bivariados
    html.H2("Análisis bivariado"),

    dcc.Graph(id="bi-1"),
    dcc.Graph(id="bi-2"),
    dcc.Graph(id="bi-3"),
    dcc.Graph(id="bi-4"),
    dcc.Graph(id="bi-5")
])


# ---------------------------------------------------------
# Actualización del dashboard
# ---------------------------------------------------------

@app.callback(
    [
        Output("kpi", "children"),
        Output("grafico-dinamico", "figure"),
        Output("uni-1", "figure"),
        Output("uni-2", "figure"),
        Output("uni-3", "figure"),
        Output("uni-4", "figure"),
        Output("uni-5", "figure"),
        Output("bi-1", "figure"),
        Output("bi-2", "figure"),
        Output("bi-3", "figure"),
        Output("bi-4", "figure"),
        Output("bi-5", "figure")
    ],
    [
        Input("selector-numerico", "value"),
        Input("selector-categorico", "value"),
        Input("filtro-anio", "value"),
        Input("filtro-municipio", "value")
    ]
)
def actualizar_dashboard(
    variable_numerica,
    variable_categorica,
    anio_seleccionado,
    municipio_seleccionado
):

    datos = datos_dashboard.copy()

    # -----------------------------------------------------
    # Aplicar filtros
    # -----------------------------------------------------

    if anio_seleccionado != "todos":
        datos = datos[
            datos["ANIO-DATOS-LIMPIO"] == anio_seleccionado
        ]

    if municipio_seleccionado != "todos":
        datos = datos[
            datos["MUN-COMERCIAL"] == municipio_seleccionado
        ]

    # -----------------------------------------------------
    # KPI
    # -----------------------------------------------------

    total = len(datos)

    kpi = f"Total de establecimientos: {total:,}"

    # -----------------------------------------------------
    # Gráfico dinámico
    # -----------------------------------------------------

    datos_numericos = datos.dropna(
        subset=[variable_numerica]
    )

    if variable_categorica == "MUN-COMERCIAL":

        resumen_dinamico = (
            datos_numericos
            .groupby(variable_numerica)
            .size()
            .reset_index(name="Cantidad")
        )

        grafico_dinamico = px.bar(
            resumen_dinamico,
            x=variable_numerica,
            y="Cantidad",
            title="Distribución de establecimientos según la variable seleccionada",
            labels={
                variable_numerica: "Variable numérica",
                "Cantidad": "Número de establecimientos"
            }
        )

    else:

        resumen_dinamico = (
            datos_numericos["ACTIVIDAD"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        resumen_dinamico.columns = [
            "Actividad",
            "Cantidad"
        ]

        grafico_dinamico = px.bar(
            resumen_dinamico,
            x="Cantidad",
            y="Actividad",
            orientation="h",
            title="Principales actividades económicas",
            labels={
                "Actividad": "Actividad económica",
                "Cantidad": "Número de establecimientos"
            }
        )

    # -----------------------------------------------------
    # UNIVARIADO 1
    # -----------------------------------------------------

    resumen = (
        datos["MUN-COMERCIAL"]
        .value_counts()
        .reset_index()
    )

    resumen.columns = ["Municipio", "Cantidad"]

    uni_1 = px.bar(
        resumen,
        x="Municipio",
        y="Cantidad",
        title="Cantidad de establecimientos por municipio",
        labels={
            "Municipio": "Municipio",
            "Cantidad": "Número de establecimientos"
        }
    )

    uni_1.update_layout(xaxis_tickangle=-45)

    # -----------------------------------------------------
    # UNIVARIADO 2
    # -----------------------------------------------------

    resumen = (
        datos["ANIO-DATOS-LIMPIO"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
        .reset_index()
    )

    resumen.columns = ["Año", "Cantidad"]

    uni_2 = px.bar(
        resumen,
        x="Año",
        y="Cantidad",
        title="Cantidad de establecimientos por año de los datos",
        labels={
            "Año": "Año de los datos",
            "Cantidad": "Número de establecimientos"
        },
        text="Cantidad"
    )

    # -----------------------------------------------------
    # UNIVARIADO 3
    # -----------------------------------------------------

    resumen = (
        datos["ULT-ANO_REN-LIMPIO"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
        .reset_index()
    )

    resumen.columns = [
        "Año de renovación",
        "Cantidad"
    ]

    uni_3 = px.bar(
        resumen,
        x="Año de renovación",
        y="Cantidad",
        title="Cantidad de establecimientos por año de última renovación",
        labels={
            "Año de renovación": "Año de última renovación",
            "Cantidad": "Número de establecimientos"
        },
        text="Cantidad"
    )

    # -----------------------------------------------------
    # UNIVARIADO 4
    # -----------------------------------------------------

    resumen = (
        datos["ACTIVIDAD"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    resumen.columns = [
        "Actividad",
        "Cantidad"
    ]

    uni_4 = px.bar(
        resumen,
        x="Cantidad",
        y="Actividad",
        orientation="h",
        title="Top 10 de actividades económicas",
        labels={
            "Actividad": "Actividad económica",
            "Cantidad": "Número de establecimientos"
        }
    )

    # -----------------------------------------------------
    # UNIVARIADO 5
    # -----------------------------------------------------

    resumen = (
        datos["FEC-MATRICULA-LIMPIA"]
        .dropna()
        .dt.year
        .value_counts()
        .sort_index()
        .reset_index()
    )

    resumen.columns = [
        "Año de matrícula",
        "Cantidad"
    ]

    uni_5 = px.line(
        resumen,
        x="Año de matrícula",
        y="Cantidad",
        markers=True,
        title="Cantidad de establecimientos por año de matrícula",
        labels={
            "Año de matrícula": "Año de matrícula",
            "Cantidad": "Número de establecimientos"
        }
    )

    # -----------------------------------------------------
    # BIVARIADO 1
    # -----------------------------------------------------

    resumen = (
        datos
        .dropna(subset=["ULT-ANO_REN-LIMPIO"])
        .groupby([
            "MUN-COMERCIAL",
            "ULT-ANO_REN-LIMPIO"
        ])
        .size()
        .reset_index(name="Cantidad")
    )

    resumen["ULT-ANO_REN-LIMPIO"] = (
        resumen["ULT-ANO_REN-LIMPIO"]
        .astype(int)
        .astype(str)
    )

    bi_1 = px.bar(
        resumen,
        x="MUN-COMERCIAL",
        y="Cantidad",
        color="ULT-ANO_REN-LIMPIO",
        barmode="group",
        title="Establecimientos por municipio y año de última renovación",
        labels={
            "MUN-COMERCIAL": "Municipio",
            "Cantidad": "Número de establecimientos",
            "ULT-ANO_REN-LIMPIO": "Año de última renovación"
        }
    )

    bi_1.update_layout(xaxis_tickangle=-45)

    # -----------------------------------------------------
    # BIVARIADO 2
    # -----------------------------------------------------

    resumen = (
        datos
        .dropna(subset=["ANIO-DATOS-LIMPIO"])
        .groupby([
            "MUN-COMERCIAL",
            "ANIO-DATOS-LIMPIO"
        ])
        .size()
        .reset_index(name="Cantidad")
    )

    resumen["ANIO-DATOS-LIMPIO"] = (
        resumen["ANIO-DATOS-LIMPIO"]
        .astype(int)
        .astype(str)
    )

    bi_2 = px.bar(
        resumen,
        x="MUN-COMERCIAL",
        y="Cantidad",
        color="ANIO-DATOS-LIMPIO",
        barmode="group",
        title="Establecimientos por municipio y año de los datos",
        labels={
            "MUN-COMERCIAL": "Municipio",
            "Cantidad": "Número de establecimientos",
            "ANIO-DATOS-LIMPIO": "Año de los datos"
        }
    )

    bi_2.update_layout(xaxis_tickangle=-45)

    # -----------------------------------------------------
    # BIVARIADO 3
    # -----------------------------------------------------

    top_actividades = (
        datos["ACTIVIDAD"]
        .value_counts()
        .head(10)
        .index
    )

    top_municipios = (
        datos["MUN-COMERCIAL"]
        .value_counts()
        .head(5)
        .index
    )

    resumen = datos[
        datos["ACTIVIDAD"].isin(top_actividades)
        & datos["MUN-COMERCIAL"].isin(top_municipios)
    ].groupby([
        "ACTIVIDAD",
        "MUN-COMERCIAL"
    ]).size().reset_index(name="Cantidad")

    bi_3 = px.bar(
        resumen,
        x="ACTIVIDAD",
        y="Cantidad",
        color="MUN-COMERCIAL",
        barmode="group",
        title="Principales actividades económicas por municipio",
        labels={
            "ACTIVIDAD": "Actividad económica",
            "Cantidad": "Número de establecimientos",
            "MUN-COMERCIAL": "Municipio"
        }
    )

    bi_3.update_layout(
        xaxis_tickangle=-45,
        height=600
    )

    # -----------------------------------------------------
    # BIVARIADO 4
    # -----------------------------------------------------

    datos_matricula = datos.dropna(
        subset=["FEC-MATRICULA-LIMPIA"]
    ).copy()

    datos_matricula["ANIO_MATRICULA"] = (
        datos_matricula["FEC-MATRICULA-LIMPIA"].dt.year
    )

    top_municipios = (
        datos["MUN-COMERCIAL"]
        .value_counts()
        .head(5)
        .index
    )

    resumen = (
        datos_matricula
        .groupby([
            "ANIO_MATRICULA",
            "MUN-COMERCIAL"
        ])
        .size()
        .reset_index(name="Cantidad")
    )

    resumen = resumen[
        resumen["MUN-COMERCIAL"].isin(top_municipios)
    ]

    bi_4 = px.line(
        resumen,
        x="ANIO_MATRICULA",
        y="Cantidad",
        color="MUN-COMERCIAL",
        markers=True,
        title="Evolución de las matrículas por año y municipio",
        labels={
            "ANIO_MATRICULA": "Año de matrícula",
            "Cantidad": "Número de establecimientos",
            "MUN-COMERCIAL": "Municipio"
        }
    )

    # -----------------------------------------------------
    # BIVARIADO 5
    # -----------------------------------------------------

    resumen = (
        datos
        .dropna(subset=[
            "ANIO-DATOS-LIMPIO",
            "ULT-ANO_REN-LIMPIO"
        ])
        .groupby([
            "ANIO-DATOS-LIMPIO",
            "ULT-ANO_REN-LIMPIO"
        ])
        .size()
        .reset_index(name="Cantidad")
    )

    resumen["ANIO-DATOS-LIMPIO"] = (
        resumen["ANIO-DATOS-LIMPIO"]
        .astype(int)
        .astype(str)
    )

    resumen["ULT-ANO_REN-LIMPIO"] = (
        resumen["ULT-ANO_REN-LIMPIO"]
        .astype(int)
        .astype(str)
    )

    bi_5 = px.bar(
        resumen,
        x="ANIO-DATOS-LIMPIO",
        y="Cantidad",
        color="ULT-ANO_REN-LIMPIO",
        barmode="group",
        title="Establecimientos por año de los datos y año de última renovación",
        labels={
            "ANIO-DATOS-LIMPIO": "Año de los datos",
            "Cantidad": "Número de establecimientos",
            "ULT-ANO_REN-LIMPIO": "Año de última renovación"
        },
        text="Cantidad"
    )

    # -----------------------------------------------------
    # Devolver resultados al dashboard
    # -----------------------------------------------------

    return (
        kpi,
        grafico_dinamico,
        uni_1,
        uni_2,
        uni_3,
        uni_4,
        uni_5,
        bi_1,
        bi_2,
        bi_3,
        bi_4,
        bi_5
    )




# Servidor Flask que utiliza Gunicorn en producción
server = app.server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
