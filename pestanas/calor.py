"""Pestaña: Mapa de calor interactivo (pico o nacionalidad por década)."""
import plotly.graph_objects as go
from shiny import module, ui
from shinywidgets import output_widget, render_widget

from src.datos import cargar_datos

FILAS = {"peak_name": "Pico", "citizenship": "Nacionalidad"}
METRICAS = {
    "n": "Número de integrantes",
    "success": "Tasa de éxito (%)",
    "oxygen_used": "Uso de oxígeno (%)",
    "died": "Tasa de mortalidad (%)",
}
MIN_N = 10  #Las tasas con menos de 10 integrantes se ocultan celdas  
FILAS_MOSTRADAS = 15
ESCALA_AZUL = [
    [0, "#c6dbef"],
    [0.25, "#9ecae1"],
    [0.5, "#6baed6"],
    [0.75, "#3182bd"],
    [1, "#08519c"],
]


@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Mapa de calor"),
        ui.layout_columns(
            ui.input_select("metrica", "Mostrar", METRICAS, selected="success"),
            ui.input_select("filas", "Por", FILAS),
            col_widths=[6, 6],
        ),
        ui.div(
            ui.strong("Nota: "),
            f"las celdas vacías en las métricas porcentuales tienen menos de "
            f"{MIN_N} integrantes por lo que no representan un 0 %.",
            class_="alert alert-info py-2 mb-2",
        ),
        output_widget("mapa"),
        full_screen=True,
    )


@module.server
def panel_server(input, output, session):
    # cargar_datos()
    members, _, _ = cargar_datos()

    @render_widget
    def mapa():
        fila, metrica = input.filas(), input.metrica()

        d = members.dropna(subset=[fila, "year"]).copy()
        d["decada"] = ((d["year"].astype(int) // 10) * 10).astype(str) + "s"

        # Las filas más frecuentes (top N)
        filas = d[fila].value_counts().head(FILAS_MOSTRADAS).index.tolist()
        d = d[d[fila].isin(filas)]
        decadas = sorted(d["decada"].unique())

        grp = d.groupby([fila, "decada"])
        n = (
            grp.size().unstack("decada")
            .reindex(index=filas, columns=decadas).fillna(0).astype(int)
        )
        if metrica == "n":
            z = n.where(n > 0)
        else:
            tasa = d[metrica].astype(float) * 100
            z = (
                tasa.groupby([d[fila], d["decada"]]).mean().unstack("decada")
                .reindex(index=filas, columns=decadas)
            )
            z = z.where(n >= MIN_N)

        z_data = z.astype(object).where(z.notna(), None).values.tolist()
        fmt = ",.0f" if metrica == "n" else ".1f"
        etiqueta = METRICAS[metrica]

        fig = go.Figure(
            go.Heatmap(
                z=z_data,
                x=z.columns.tolist(),
                y=z.index.tolist(),
                zmin=0 if metrica != "n" else None,
                zmax=100 if metrica != "n" else None,
                customdata=n.values,
                colorscale=ESCALA_AZUL,
                hoverongaps=False,
                xgap=1,
                ygap=1,
                hovertemplate=(
                    f"<b>%{{y}}</b> · %{{x}}<br>{etiqueta}: %{{z:{fmt}}}"
                    "<br>Integrantes: %{customdata:,}<extra></extra>"
                ),
                colorbar=dict(title=etiqueta),
            )
        )
        fig.update_xaxes(type="category", title="Década")
        fig.update_yaxes(type="category", title=FILAS[fila], autorange="reversed")
        fig.update_layout(
            height=max(400, 26 * len(filas) + 150),
            plot_bgcolor="#F3F4F6",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        return fig
