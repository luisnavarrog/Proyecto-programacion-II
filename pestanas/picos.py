"""Pestaña: Picos."""
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
            max=int(expeditions.dropna(subset=["peak_name"])["peak_id"].nunique()),
            value=10,
            step=1,
        ),
        ui.div(
            output_widget("grafico_picos"),
            class_="overflow-auto",
            style="max-height: 650px",
        ),
        ui.hr(),
        ui.h4("¿Las montañas más altas registran más expediciones?"),
        ui.p(
            "Cada punto representa una montaña. Pasa el cursor para consultar "
            "su nombre, elevación y expediciones en el período y temporada elegidos."
        ),
        output_widget("dispersion_picos"),
        ui.p(
            "Incluye montañas sin expediciones registradas. "
            "Pearson y la recta describen la asociación, sin demostrar causalidad.",
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

            return grafico
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
        grafico.update_layout(height=max(400, 28 * len(top_picos) + 100))

        return grafico

    @render_widget
    def dispersion_picos():
        # Aplicar los mismos filtros que al ranking
        expediciones_filtradas = expeditions[
            (expeditions["year"] >= input.anios()[0])
            & (expeditions["year"] <= input.anios()[1])
        ]
        if input.temporada() != "Todas":
            expediciones_filtradas = expediciones_filtradas[
                expediciones_filtradas["season"] == input.temporada()
            ]

        # Contar antes de unir para conservar una fila por montaña
        conteo = expediciones_filtradas.groupby("peak_id").size()
        conteo = conteo.reset_index(name="cantidad")
        datos_dispersion = peaks[["peak_id", "peak_name", "height_metres"]].merge(
            conteo, on="peak_id", how="left", validate="one_to_one"
        )
        datos_dispersion["cantidad"] = datos_dispersion["cantidad"].fillna(0).astype(int)
        datos_dispersion = datos_dispersion.dropna(subset=["height_metres"])

        grafico = px.scatter(
            datos_dispersion,
            x="height_metres",
            y="cantidad",
            hover_name="peak_name",
            hover_data={"height_metres": ":.0f", "cantidad": ":d"},
            labels={
                "height_metres": "Elevación sobre el nivel del mar (m)",
                "cantidad": "Expediciones registradas",
            },
            template="plotly_white",
            color_discrete_sequence=["#426789"],
        )
        grafico.update_traces(
            marker={"size": 9, "opacity": 0.7, "line": {"width": 0.7, "color": "white"}}
        )
        # Calcular Pearson y la recta con las mismas montañas del gráfico
        x = datos_dispersion["height_metres"]
        y = datos_dispersion["cantidad"]
        texto_correlacion = "Pearson: no calculable, sin variación suficiente"
        if len(datos_dispersion) >= 2 and x.nunique() > 1 and y.nunique() > 1:
            correlacion = x.corr(y)
            texto_correlacion = f"Pearson r = {correlacion:.3f}".replace(".", ",")

            # Mínimos cuadrados: pendiente = covarianza / varianza
            pendiente = x.cov(y) / x.var()
            intercepto = y.mean() - pendiente * x.mean()
            extremos_x = [x.min(), x.max()]
            extremos_y = [
                intercepto + pendiente * x.min(),
                intercepto + pendiente * x.max(),
            ]
            grafico.add_trace(
                go.Scatter(
                    x=extremos_x,
                    y=extremos_y,
                    mode="lines",
                    name="Recta de regresión",
                    line={"color": "#c57845", "width": 2, "dash": "dash"},
                    hovertemplate=(
                        "Recta de regresión<br>Elevación: %{x:.0f} m"
                        "<br>Valor ajustado: %{y:.1f}<extra></extra>"
                    ),
                )
            )
        grafico.add_annotation(
            x=0, y=1.2, xref="paper", yref="paper", xanchor="left",
            text=f"<b>{texto_correlacion}</b>", showarrow=False,
        )
        grafico.update_layout(
            height=480,
            margin={"l": 60, "r": 25, "t": 90, "b": 60},
            showlegend=False,
            font={"family": "sans-serif", "color": "#24445f"},
            hoverlabel={"bgcolor": "white"},
        )
        grafico.update_xaxes(gridcolor="#edf2f6", tickformat="d")
        grafico.update_yaxes(gridcolor="#edf2f6", rangemode="tozero", tickformat="d")
        sin_expediciones = int((datos_dispersion["cantidad"] == 0).sum())
        grafico.add_annotation(
            x=0, y=1.1, xref="paper", yref="paper", xanchor="left",
            text=f"{len(datos_dispersion)} montañas · {sin_expediciones} sin expediciones para estos filtros",
            showarrow=False,
        )
        return grafico

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
                        class_="col-12 order-2" if len(seleccion) == 2 else "col-12 col-md-4",
                    ),
                    ui.div(
                        ilustracion,
                        class_="col-12 order-1" if len(seleccion) == 2 else "col-12 col-md-8",
                    ),
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
