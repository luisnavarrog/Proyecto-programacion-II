"""Pestaña: Mapa de calor interactivo (pico o nacionalidad por década o estación)."""
from numbers import Integral

import pandas as pd
import plotly.graph_objects as go
from shiny import module, reactive, ui
from shinywidgets import output_widget, render_widget
from src.datos import cargar_datos

#Variable para definir las filas del mapa
FILAS = {"peak_name": "Pico", "citizenship": "Nacionalidad"}

#Variable para definir las columnas del mapa
PERIODOS = {"decada": "Década", "estacion": "Estación del año"}

#Las estaciones del año en español, para mostrar en el mapa de calor
ESTACIONES = {
    "Spring": "Primavera",
    "Summer": "Verano",
    "Autumn": "Otoño",
    "Winter": "Invierno",
}
ORDEN_ESTACIONES = list(ESTACIONES.values())
ANTES_1950 = "<1950"  # todo lo anterior a 1950 se agrupa en una columna

# Cantidad de filas mostradas (las más frecuentes, ordenadas de mayor a menor)
TOP_N = 10
# Mínimo de integrantes por celda para mostrar una tasa (muestras pequeñas se ocultan)
MIN_N = 5

# Configuración de cada métrica: nombre, escala de color, formato y máximo fijo
METRICAS = {
    "success": dict(nombre="Tasa de éxito", escala="Mint", sufijo=" %", fmt=".0f", zmax=100),
    "died": dict(nombre="Tasa de mortalidad", escala="Reds", sufijo=" %", fmt=".1f", zmax=None),
    "oxygen_used": dict(nombre="Uso de oxígeno", escala="Greys", sufijo=" %", fmt=".0f", zmax=100),
    "n": dict(nombre="Número de integrantes", escala="Blues", sufijo="", fmt=",.0f", zmax=None),
}

COLOR_VACIO = "#E5E7EB"  # celdas sin datos suficientes

def preparar_base(members: pd.DataFrame) -> pd.DataFrame:
    """Añade las columnas 'decada' y 'estacion' una sola vez."""
    base = members.dropna(subset=["year"]).copy()
    base = base[base["year"] >= 1950]  # se descartan los años anteriores a 1950
    anio = base["year"].astype(int)

    base["decada"] = (anio // 10 * 10).astype(str) + "s"

    base["estacion"] = base["season"].map(ESTACIONES)  # lo desconocido queda como NaN
    return base


def ordenar_columnas(columnas, periodo: str) -> list:
    """Orden cronológico de las columnas (el orden alfabético no sirve con '<1950')."""
    if periodo == "estacion":
        return [c for c in ORDEN_ESTACIONES if c in columnas]
    resto = sorted(c for c in columnas if c != ANTES_1950)
    return ([ANTES_1950] if ANTES_1950 in columnas else []) + resto


def construir_tabla(
    base: pd.DataFrame, fila: str, metrica: str, periodo: str, min_n: int, top_n: int,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Devuelve (z, n): valor de la métrica y número de integrantes por celda."""
    d = base.dropna(subset=[fila, periodo])

    # Las filas más frecuentes, de mayor a menor
    top = d[fila].value_counts().head(top_n).index.tolist()
    d = d[d[fila].isin(top)]
    if d.empty:
        return None, None

    # Número de integrantes por fila y periodo
    n = d.groupby([fila, periodo]).size().unstack(periodo, fill_value=0)
    n = n.reindex(index=[f for f in top if f in n.index],
                  columns=ordenar_columnas(list(n.columns), periodo))

    if metrica == "n":
        z = n.where(n > 0)
    else:
        tasa = d[metrica].astype(float) * 100
        z = tasa.groupby([d[fila], d[periodo]]).mean().unstack(periodo)
        z = z.reindex(index=n.index, columns=n.columns)
        z = z.where(n >= min_n)  # se ocultan celdas con muestra pequeña

    columnas_ok = z.columns[z.notna().any(axis=0)]
    filas_ok = z.index[z.notna().any(axis=1)]
    z = z.loc[filas_ok, columnas_ok]
    n = n.loc[filas_ok, columnas_ok]
    if z.empty:
        return None, None

    return z, n


def figura_vacia(mensaje: str) -> go.FigureWidget:
    """Figura con un mensaje cuando no hay datos para la selección."""
    fig = go.FigureWidget()
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        annotations=[dict(text=mensaje, showarrow=False, font=dict(size=16))],
        height=300,
    )
    return fig


@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Mapa de calor"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select(
                    "metrica", "Indicador",
                    {k: v["nombre"] for k, v in METRICAS.items()},
                    selected="success",
                ),
                ui.input_select("filas", "Agrupar por", FILAS),
                ui.input_select("periodo", "Período", PERIODOS),
                ui.input_select(
                    "cantidad",
                    "Cantidad de filas",
                    {"5": "5", "10": "10", "20": "20"},
                    selected="10",
                ),
                ui.help_text(
                    "Se muestran los grupos con más integrantes, "
                    "según la cantidad seleccionada. "
                    "Las celdas grises indican ausencia de datos "
                    f"o menos de {MIN_N} integrantes en las tasas. "
                ),
                width=300,
            ),
            output_widget("mapa"),
        ),
        full_screen=True,
    )


@module.server
def panel_server(input, output, session):
    members, _, _ = cargar_datos()
    base = preparar_base(members)  # se prepara una sola vez

    @reactive.calc
    def tabla():
        return construir_tabla(
            base,
            input.filas(),
            input.metrica(),
            input.periodo(),
            MIN_N,
            int(input.cantidad()),
        )

    @render_widget
    def mapa():
        z, n = tabla()
        if z is None or n is None:
            return figura_vacia("No hay datos para esta selección")

        cfg = METRICAS[input.metrica()]
        fmt = cfg["fmt"]

        fila = input.filas()
        periodo = input.periodo()

        nombre_fila = "pico" if fila == "peak_name" else "nacionalidad"
        nombre_periodo = "década" if periodo == "decada" else "estación del año"
        tipo_filas = "picos" if fila == "peak_name" else "nacionalidades"

        titulo = f"{cfg['nombre']} por {nombre_fila} y {nombre_periodo}"
        subtitulo = f"Selección de los {input.cantidad()} {tipo_filas} con más integrantes"

        # None en lugar de NaN para que Plotly deje la celda vacía
        z_data = z.astype(object).where(z.notna(), None).values.tolist()

        textos = [
            [
                f"{valor:{fmt}}{cfg['sufijo']}" if valor is not None else ""
                for valor in fila
            ]
            for fila in z_data
        ]
                
        mensajes = []

        for i, nombre in enumerate(z.index):
            fila_mensajes = []

            for j, columna in enumerate(z.columns):
                conteo = n.iloc[i, j]
                if not isinstance(conteo, Integral):
                    raise TypeError(
                        f"Se esperaba un conteo entero; se obtuvo "
                        f"{type(conteo).__name__}"
                    )
                cantidad = int(conteo)
                valor = z_data[i][j]

                if cantidad == 0:
                    detalle = "Sin integrantes registrados"
                elif valor is None and cantidad < MIN_N:
                    detalle = (
                        f"Tasa oculta: menos de {MIN_N} integrantes"
                    )
                elif valor is None:
                    detalle = "Sin datos disponibles para esta métrica"
                else:
                    detalle = (
                        f"{cfg['nombre']}: "
                        f"{valor:{fmt}}{cfg['sufijo']}"
                    )

                fila_mensajes.append(
                    f"<b>{nombre}</b> · {columna}<br>"
                    f"{detalle}<br>Integrantes: {cantidad:,}"
                )

            mensajes.append(fila_mensajes)

        fig = go.FigureWidget(
            go.Heatmap(
                z=z_data,
                x=z.columns.tolist(),
                y=z.index.tolist(),
                customdata=n.values,
                colorscale=cfg["escala"],
                zmin=0,
                zmax=cfg["zmax"],
                xgap=2,
                ygap=2,
                hoverongaps=True,
                text=textos,
                texttemplate="%{text}",
                textfont=dict(size=11),
                hovertext=mensajes,
                hovertemplate="%{hovertext}<extra></extra>",
                colorbar=dict(
                    title=cfg["nombre"],
                    thickness=14,
                    ticksuffix=cfg["sufijo"],
                ),
            )
        )
        fig.update_xaxes(type="category", title=PERIODOS[input.periodo()], side="bottom")
        fig.update_yaxes(
            type="category",
            title=FILAS[input.filas()],
            autorange="reversed",
            automargin=True,
        )
        fig.update_layout(
            font=dict(color="#FFFFFF"),
            title=dict(
                text=f"{titulo}<br><sup>{subtitulo}</sup>",
                x=0,
                xanchor="left",
            ),
            height=max(420, 30 * len(z) + 160),
            plot_bgcolor=COLOR_VACIO,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=85, b=10),
        )
        return fig