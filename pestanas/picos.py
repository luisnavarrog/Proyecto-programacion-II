"""Pestaña: Picos."""
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, render, ui
from shinywidgets import output_widget, render_widget

from src.datos import cargar_datos
from src.ilustraciones import preparar_ilustracion


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
        ui.h4("Explora y compara montañas"),
        ui.input_selectize(
            "pico",
            "Seleccioná una o dos montañas",
            choices=opciones_picos,
            selected=["EVER"],
            multiple=True,
            remove_button=True,
            options={"maxItems": 2},
        ),
        ui.output_ui("comparacion_alturas"),
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
        seleccion = list(input.pico() or [])[:2]
        if not seleccion:
            return ui.p("Seleccioná una montaña para consultar su ficha.")

        fichas = []
        for identificador in seleccion:
            pico = peaks[peaks["peak_id"] == identificador].iloc[0]

            altura = "No disponible"
            if pd.notna(pico["height_metres"]):
                altura = f'{int(pico["height_metres"])} m'

            primer_ascenso = "No disponible"
            if pd.notna(pico["first_ascent_year"]):
                primer_ascenso = str(int(pico["first_ascent_year"]))

            # Seleccionar las expediciones de la montaña y el período
            expediciones_pico = expeditions[
                (expeditions["peak_id"] == identificador)
                & (expeditions["year"] >= input.anios()[0])
                & (expeditions["year"] <= input.anios()[1])
            ]

            # Aplicar la temporada seleccionada
            if input.temporada() != "Todas":
                expediciones_pico = expediciones_pico[
                    expediciones_pico["season"] == input.temporada()
                ]

            cantidad = len(expediciones_pico)

            ilustracion = preparar_ilustracion(
                identificador, pico["peak_name"], altura
            )

            ficha = ui.card(
                ui.div(
                    ui.div(
                        ui.h3(pico["peak_name"]),
                        ui.tags.dl(
                            ui.tags.dt("Elevación sobre el nivel del mar"),
                            ui.tags.dd(altura, class_="fs-3 text-primary"),
                            ui.tags.dt("Primer ascenso registrado"),
                            ui.tags.dd(primer_ascenso, class_="fs-4"),
                            ui.tags.dt("Expediciones"),
                            ui.tags.dd(str(cantidad), class_="fs-3 text-primary"),
                        ),
                        ui.p(
                            "La cantidad de expediciones corresponde al período "
                            "y la temporada seleccionados.",
                            class_="small text-muted",
                        ),
                        class_="col-12 col-md-4",
                    ),
                    ui.div(
                        ilustracion,
                        class_="col-12 col-md-8",
                    ),
                    class_="row g-4 align-items-center",
                ),
            )
            columna = "col-12 col-xl-6" if len(seleccion) == 2 else "col-12"
            fichas.append(ui.div(ficha, class_=columna))

        return ui.div(*fichas, class_="row g-3")

    @render.ui
    def comparacion_alturas():
        seleccion = list(input.pico() or [])[:2]
        if len(seleccion) != 2:
            return None

        primero = peaks[peaks["peak_id"] == seleccion[0]].iloc[0]
        segundo = peaks[peaks["peak_id"] == seleccion[1]].iloc[0]
        if pd.isna(primero["height_metres"]) or pd.isna(segundo["height_metres"]):
            return ui.p("No hay elevaciones disponibles para comparar ambos picos.")

        altura_1 = int(primero["height_metres"])
        altura_2 = int(segundo["height_metres"])
        diferencia = abs(altura_1 - altura_2)
        nombre_1 = escape(str(primero["peak_name"]))
        nombre_2 = escape(str(segundo["peak_name"]))
        ancho_1 = altura_1 / 9000 * 520
        ancho_2 = altura_2 / 9000 * 520

        # Barras con origen en cero y la misma escala para ambos picos
        comparacion = f"""
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 170"
                 width="100%" role="img"
                 aria-label="Elevaciones sobre el nivel del mar. {nombre_1}: {altura_1} metros.
                 {nombre_2}: {altura_2} metros. Diferencia: {diferencia} metros.">
                <g font-family="sans-serif" font-size="17" fill="#24445f">
                    <text x="10" y="49">{nombre_1}</text>
                    <text x="10" y="104">{nombre_2}</text>
                    <rect x="230" y="25" width="{ancho_1}" height="34" rx="5" fill="#426789"/>
                    <rect x="230" y="80" width="{ancho_2}" height="34" rx="5" fill="#7399bb"/>
                    <text x="{240 + ancho_1}" y="49">{altura_1} m</text>
                    <text x="{240 + ancho_2}" y="104">{altura_2} m</text>
                    <path d="M230 125 H750" stroke="#aabcca"/>
                    <text x="230" y="151" text-anchor="middle">0</text>
                    <text x="403.33" y="151" text-anchor="middle">3000</text>
                    <text x="576.67" y="151" text-anchor="middle">6000</text>
                    <text x="750" y="151" text-anchor="middle">9000 m</text>
                </g>
            </svg>
        """
        return ui.card(
            ui.h4("Comparación de elevaciones"),
            ui.HTML(comparacion),
            ui.p(f"Diferencia de elevación: {diferencia} m."),
            ui.p(
                "Las barras comparten escala desde el nivel del mar. "
                "Las siluetas de las fichas son ilustrativas y tienen acercamiento.",
                class_="small text-muted",
            ),
        )
