"""Pestaña: Picos."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import module, render, ui
from shinywidgets import output_widget, render_widget

from src.datos import cargar_datos
from src.ilustraciones import preparar_ilustracion
from src.tema import (
    COLORES_RANGOS,
    GLACIAR,
    PANEL,
    TEXTO,
    aplicar_tema,
)


members, expeditions, peaks = cargar_datos()

# Preparar las opciones del selector en orden alfabético
picos_ordenados = peaks.sort_values("peak_name")
opciones_picos = dict(
    zip(picos_ordenados["peak_id"], picos_ordenados["peak_name"])
)

@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Picos: expediciones y elevación"),
        ui.div(
            ui.div(
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
                class_="col-12 col-md-8",
            ),
            ui.div(
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
                class_="col-12 col-md-4",
            ),
            class_="row g-3 align-items-end",
        ),
        ui.h4("¿Cuáles tienen más expediciones?"),
        ui.input_slider(
            "numero_picos",
            "Cantidad de montañas en el gráfico",
            min=1,
            max=min(
                30,
                int(expeditions.dropna(subset=["peak_name"])["peak_id"].nunique()),
            ),
            value=10,
            step=1,
        ),
        ui.div(
            output_widget("grafico_picos"),
            class_="overflow-auto",
            style="max-height: 650px",
        ),
        ui.hr(),
        ui.h4("¿Dónde se concentran las expediciones?"),
        ui.p(
            "Compara la distribución de las montañas y las expediciones "
            "por rango de elevación. Pasa el cursor para consultar las cantidades."
        ),
        output_widget("proporciones_altura"),
        ui.p(
            "El catálogo es una referencia fija. Las expediciones cambian con "
            "el período y la temporada seleccionados. Cada barra con datos suma 100 %.",
            class_="small text-muted",
        ),
        ui.hr(),
        ui.h4("Explora y compara montañas"),
        ui.input_selectize(
            "pico",
            "Selecciona una o dos montañas",
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

            return aplicar_tema(grafico)
        # Contar las expediciones por montaña
        conteo_picos = expediciones_filtradas.groupby(
            ["peak_id", "peak_name"]
        ).size()
        conteo_picos = conteo_picos.reset_index(name="cantidad")

        # Seleccionar la cantidad de montañas elegida
        conteo_picos = conteo_picos.sort_values(
            "cantidad", ascending=False
        )
        top_picos = conteo_picos.head(input.numero_picos())
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
        grafico.update_traces(marker_color=GLACIAR)
        grafico.update_layout(height=max(400, 28 * len(top_picos) + 100))

        return aplicar_tema(grafico)

    @render_widget
    def proporciones_altura():
        # Aplicar el período y la temporada a las expediciones
        expediciones_filtradas = expeditions[
            (expeditions["year"] >= input.anios()[0])
            & (expeditions["year"] <= input.anios()[1])
        ]
        if input.temporada() != "Todas":
            expediciones_filtradas = expediciones_filtradas[
                expediciones_filtradas["season"] == input.temporada()
            ]

        # Clasificar el catálogo sin cambiar los datos compartidos
        rangos = [
            "Menos de 6000 m",
            "6000 a menos de 7000 m",
            "7000 a menos de 8000 m",
            "8000 m o más",
        ]
        catalogo = peaks[["peak_id", "height_metres"]].copy()
        catalogo["rango"] = pd.cut(
            catalogo["height_metres"],
            bins=[0, 6000, 7000, 8000, float("inf")],
            labels=rangos,
            right=False,
        )
        expediciones_altura = expediciones_filtradas[["peak_id"]].merge(
            catalogo[["peak_id", "rango"]],
            on="peak_id", how="left", validate="many_to_one",
        )
        conteo_catalogo = catalogo["rango"].value_counts().reindex(rangos, fill_value=0)
        conteo_expediciones = expediciones_altura["rango"].value_counts().reindex(
            rangos, fill_value=0
        )
        total_catalogo = int(conteo_catalogo.sum())
        total_expediciones = int(conteo_expediciones.sum())
        sin_altura = len(expediciones_filtradas) - total_expediciones

        colores = COLORES_RANGOS
        grafico = go.Figure()
        inicio_catalogo = 0
        inicio_expediciones = 0
        for rango, color in zip(rangos, colores):
            cantidades = [int(conteo_catalogo[rango]), int(conteo_expediciones[rango])]
            porcentajes = [
                cantidades[0] / total_catalogo * 100 if total_catalogo else 0,
                cantidades[1] / total_expediciones * 100 if total_expediciones else 0,
            ]
            etiquetas = [f"{valor:.1f} %".replace(".", ",") for valor in porcentajes]
            grafico.add_trace(go.Bar(
                x=porcentajes,
                y=[1, 0],
                orientation="h",
                name=rango,
                marker_color=color,
                width=0.34,
                customdata=list(zip(cantidades, etiquetas)),
                text=[etiqueta if valor >= 8 else "" for valor, etiqueta in zip(porcentajes, etiquetas)],
                textposition="inside",
                insidetextanchor="middle",
                textfont={"color": TEXTO, "size": 15},
                hovertemplate=(
                    f"<b>{rango}</b><br>"
                    "%{customdata[0]} registros<br>"
                    "%{customdata[1]} del total de su grupo<extra></extra>"
                ),
            ))
            # Etiquetar los segmentos pequeños sobre la barra sin agrandarlos
            for y, inicio, valor, etiqueta in zip(
                [1, 0], [inicio_catalogo, inicio_expediciones], porcentajes, etiquetas
            ):
                if 0 < valor < 8:
                    grafico.add_annotation(
                        x=inicio + valor / 2, y=y + 0.17,
                        ax=0, ay=-25, text=etiqueta,
                        showarrow=True, arrowhead=0, arrowcolor=color,
                        font={"color": TEXTO, "size": 12},
                        bgcolor=PANEL, borderpad=2,
                    )
            inicio_catalogo += porcentajes[0]
            inicio_expediciones += porcentajes[1]

        if not total_expediciones:
            mensaje = "No hay expediciones con elevación identificada para estos filtros."
            if expediciones_filtradas.empty:
                mensaje = "No hay expediciones registradas para estos filtros."
            grafico.add_annotation(
                x=50, y=0, text=mensaje, showarrow=False,
            )
        if sin_altura:
            grafico.add_annotation(
                x=0, y=-0.35, xref="paper", yref="paper", xanchor="left",
                text=f"Expediciones excluidas por falta de elevación identificada: {sin_altura}",
                showarrow=False, font={"size": 11},
            )
        grafico.update_layout(
            barmode="stack",
            height=450,
            margin={"l": 150, "r": 25, "t": 105, "b": 105},
            legend={
                "orientation": "h", "x": 0, "y": 1.65,
                "font": {"size": 12}, "traceorder": "normal",
                "itemclick": False, "itemdoubleclick": False,
            },
        )
        grafico.update_xaxes(
            range=[0, 100], tickvals=[0, 25, 50, 75, 100], ticksuffix=" %",
            title="Porcentaje del total de cada grupo", showgrid=False,
        )
        grafico.update_yaxes(
            range=[-0.45, 1.6], tickvals=[1, 0],
            ticktext=[
                f"<b>Catálogo</b><br>{total_catalogo} montañas",
                f"<b>Expediciones</b><br>{total_expediciones:,} registros".replace(",", " "),
            ],
            ticklabelstandoff=12, showgrid=False, zeroline=False,
        )
        return aplicar_tema(grafico)

    @render.ui
    def ficha_pico():
        seleccion = list(input.pico() or [])[:2]
        if not seleccion:
            return ui.p("Selecciona una montaña para consultar su ficha.")

        # En comparación se usa la misma escala para los dos dibujos
        elevaciones = peaks.loc[peaks["peak_id"].isin(seleccion), "height_metres"]
        comparar_dibujos = len(seleccion) == 2 and elevaciones.notna().all()
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
                identificador,
                pico["peak_name"],
                altura,
                elevacion_comparada=float(pico["height_metres"]) if comparar_dibujos else None,
            )

            contenido_ficha = [
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
                    class_="col-12" if ilustracion is None else (
                        "col-12 order-2" if len(seleccion) == 2 else "col-12 col-md-4"
                    ),
                )
            ]
            if ilustracion is not None:
                contenido_ficha.append(
                    ui.div(
                        ilustracion,
                        class_="col-12 order-1" if len(seleccion) == 2 else "col-12 col-md-8",
                    )
                )

            ficha = ui.card(
                ui.div(
                    *contenido_ficha,
                    class_="row g-4 align-items-center",
                ),
            )
            columna = "col-6 flex-shrink-0" if len(seleccion) == 2 else "col-12"
            fichas.append(ui.div(ficha, class_=columna, style="min-width: 280px"))

        return ui.div(*fichas, class_="row g-3 flex-nowrap overflow-auto")

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
        return ui.div(
            ui.h4("Comparación de elevaciones"),
            ui.p(f"Diferencia de elevación: {diferencia} m."),
            ui.p(
                "Los dibujos comparten una base y una escala vertical de elevación. "
                "Las formas son ilustrativas. Los filtros afectan solo las expediciones.",
                class_="small text-muted",
            ),
        )
