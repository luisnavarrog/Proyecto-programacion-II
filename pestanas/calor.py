"""Pestaña: Mapa de calor interactivo (pico o nacionalidad por década o estación)."""
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
    "n": dict(nombre="Número de integrantes", escala="Blues", sufijo="", fmt=",.0f", zmax=None),
    "success": dict(nombre="Tasa de éxito", escala="Mint", sufijo=" %", fmt=".0f", zmax=100),
    "oxygen_used": dict(nombre="Uso de oxígeno", escala="Greys", sufijo=" %", fmt=".0f", zmax=100),
    "died": dict(nombre="Tasa de mortalidad", escala="Reds", sufijo=" %", fmt=".1f", zmax=None),
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
    base: pd.DataFrame, fila: str, metrica: str, periodo: str, min_n: int,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Devuelve (z, n): valor de la métrica y número de integrantes por celda."""
    d = base.dropna(subset=[fila, periodo])

    # Las filas más frecuentes, de mayor a menor
    top = d[fila].value_counts().head(TOP_N).index.tolist()
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
                    "metrica", "Métrica",
                    {k: v["nombre"] for k, v in METRICAS.items()},
                    selected="success",
                ),
                ui.input_select("filas", "Filas", FILAS),
                ui.input_select("periodo", "Columnas", PERIODOS),
                ui.help_text(
                    f"Se muestran las {TOP_N} filas con más integrantes. "
                    "En las métricas porcentuales, las celdas grises tienen menos de  "
                    f"{MIN_N} integrantes y no significan un 0%."
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
            base, input.filas(), input.metrica(), input.periodo(), MIN_N
        )

    @render_widget
    def mapa():
        z, n = tabla()
        if z is None or n is None:
            return figura_vacia("No hay datos para esta selección")

        cfg = METRICAS[input.metrica()]
        fmt = cfg["fmt"]

        # None en lugar de NaN para que Plotly deje la celda vacía
        z_data = z.astype(object).where(z.notna(), None).values.tolist()

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
                hoverongaps=False,
                texttemplate=f"%{{z:{fmt}}}",
                textfont=dict(size=11),
                hovertemplate=(
                    "<b>%{y}</b> · %{x}<br>"
                    f"{cfg['nombre']}: %{{z:{fmt}}}{cfg['sufijo']}"
                    "<br>Integrantes: %{customdata:,}<extra></extra>"
                ),
                colorbar=dict(
                    title=cfg["nombre"], thickness=14, ticksuffix=cfg["sufijo"]
                ),
            )
        )
        fig.update_xaxes(type="category", title=PERIODOS[input.periodo()], side="bottom")
        fig.update_yaxes(
            type="category", title=FILAS[input.filas()], autorange="reversed"
        )
        fig.update_layout(
            height=max(420, 30 * len(z) + 160),
            plot_bgcolor=COLOR_VACIO,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig