"""Pestaña: Picos."""
from shiny import module, ui, render
import pandas as pd
from src.datos import cargar_datos
import plotly.express as px
import plotly.graph_objects as go
from shinywidgets import output_widget, render_widget
members, expeditions, peaks = cargar_datos()
# Preparar las opciones del selector en orden alfabético
picos_ordenados = peaks.sort_values("peak_name")
opciones_picos = dict(
    zip(picos_ordenados["peak_id"], picos_ordenados["peak_name"])
)

@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Las diez montañas con más expediciones"),
        ui.input_slider(
            "anios",
            "Período de las expediciones",
            min=int(expeditions["year"].min()),
            max=int(expeditions["year"].max()),
            value=(
                int(expeditions["year"].min()),
                int(expeditions["year"].max()),
            ),
            step=1,
            sep="",
        ),

        ui.input_select(
            "temporada",
            "Temporada",
            choices={
                "Todas": "Todas las temporadas",
                "Spring": "Primavera",
                "Summer": "Verano",
                "Autumn": "Otoño",
                "Winter": "Invierno",
                "Unknown": "Desconocida",
            },
            selected="Todas",
        ),
        output_widget("grafico_picos"),
        ui.hr(),
        ui.h4("Explora una montaña"),
        ui.input_select(
            "pico",
            "Montaña",
            choices=opciones_picos,
        ),
        ui.output_ui("ficha_pico"),
    )


@module.server
def panel_server(input, output, session):

    @render_widget
    def grafico_picos():
        # Seleccionar las expediciones dentro del período elegido
        expediciones_filtradas = expeditions[
            (expeditions["year"] >= input.anios()[0])
            & (expeditions["year"] <= input.anios()[1])
        ]
        # Filtrar por temporada cuando se elige una específica
        if input.temporada() != "Todas":
            expediciones_filtradas = expediciones_filtradas[
                expediciones_filtradas["season"] == input.temporada()
            ]
        # Mostrar un mensaje cuando los filtros no tienen registros
        if expediciones_filtradas.empty:
            grafico = go.Figure()

            grafico.add_annotation(
                text="No hay expediciones registradas para estos filtros.",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
            )

            grafico.update_xaxes(visible=False)
            grafico.update_yaxes(visible=False)

            return grafico
        # Contar las expediciones por montaña
        conteo_picos = expediciones_filtradas.groupby(
            ["peak_id", "peak_name"]
        ).size()
        conteo_picos = conteo_picos.reset_index(name="cantidad")

        # Seleccionar las diez montañas con más expediciones
        conteo_picos = conteo_picos.sort_values(
            "cantidad", ascending=False
        )
        top_picos = conteo_picos.head(10)
        grafico = px.bar(
            top_picos,
            x="cantidad",
            y="peak_name",
            orientation="h",
            labels={
                "cantidad": "Cantidad de expediciones",
                "peak_name": "Montaña",
            },
        )

        grafico.update_yaxes(autorange="reversed")

        return grafico

    @render.ui
    def ficha_pico():
        pico = peaks[peaks["peak_id"] == input.pico()].iloc[0]

        altura = "No disponible"
        if pd.notna(pico["height_metres"]):
            altura = f'{int(pico["height_metres"])} m'

        primer_ascenso = "No disponible"
        if pd.notna(pico["first_ascent_year"]):
            primer_ascenso = str(int(pico["first_ascent_year"]))

        # Seleccionar las expediciones de la montaña y el período
        expediciones_pico = expeditions[
            (expeditions["peak_id"] == input.pico())
            & (expeditions["year"] >= input.anios()[0])
            & (expeditions["year"] <= input.anios()[1])
        ]

        # Aplicar la temporada seleccionada
        if input.temporada() != "Todas":
            expediciones_pico = expediciones_pico[
                expediciones_pico["season"] == input.temporada()
            ]

        cantidad = len(expediciones_pico)

        return ui.card(
            ui.card_header(pico["peak_name"]),
            ui.p(f"Altura: {altura}"),
            ui.p(f"Primer ascenso registrado: {primer_ascenso}"),
            ui.p(f"Expediciones con los filtros seleccionados: {cantidad}"),
        )