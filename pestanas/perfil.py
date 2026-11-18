
"""Pestaña: Perfil y oxígeno."""

import pandas as pd
import plotly.graph_objects as go
from shiny import module, render, ui, reactive
from shinywidgets import output_widget, render_widget #con render muestro el grafico dentro de shiny

from src.datos import cargar_datos  #traigo la tabla de integrantes

#Menos de 20 integrantes, no se mostrara el porcentaje
MIN_N = 20


@module.ui
def panel_ui():
    # Se leen las veinte montañas con más integrantes para el selector
    members, _, _ = cargar_datos()
    top = members["peak_name"].value_counts().head(20).index.tolist()
    opciones = ["Todas las montañas"] + top

    #Es para agregar un slider bar
    anio_min = int(members["year"].min())
    anio_max = int(members["year"].max())

    return ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("montana", "Montaña", opciones, selected="Todas las montañas"),
            ui.input_slider("anio", "Año", min=anio_min, max=anio_max, value=(anio_min, anio_max), sep=""),
           # ui.p("El selector cambia solo el gráfico de éxito según oxígeno."),
        ),
        ui.card(
            ui.card_header("Pregunta 3: edades y éxito según oxígeno"),
            ui.p("¿Cómo se distribuyen las edades registradas y cómo varía el éxito según el uso de oxígeno?"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Distribución de edades"),
                    output_widget("grafico_edades"),
                ),
                ui.card(
                    ui.card_header("Éxito según uso de oxígeno"),
                    output_widget("grafico_oxigeno"),
                ),
            ),
            ui.card(
                ui.card_header("Participaciones usadas en el análisis"),
                ui.output_ui("revision"),
            ),
            ui.p("Comparación descriptiva: las diferencias pueden relacionarse con la montaña, la temporada y el período. No demuestra un efecto causal del oxígeno."),
        ),
    )


@module.server
def panel_server(input, output, session):
    members, _, _ = cargar_datos()

    @reactive.calc
    def datos_filtrados():
        #se filtra la tabla por el rango de años del slider
        rango = input.anio()
        return members[(members["year"] >= rango[0]) & (members["year"] <= rango[1])]

    @render_widget
    def grafico_edades(): #guarda solo las edades válidas (se escogio entre 15 y 90)
        tabla = datos_filtrados()

        elegida = input.montana()
        if elegida != "Todas las montañas":
            tabla = tabla[tabla["peak_name"] == elegida]

        edades=[]
        for edad in tabla["age"]:
            if pd.notna(edad) and edad >= 15 and edad <= 90:
                edades.append(edad)

        # Histograma con intervalos de 5 años
        fig = go.FigureWidget(go.Histogram(x=edades, xbins=dict(start=15, end=95, size=5)))
        fig.update_layout(
            title="Distribución de edades",
            xaxis_title="Edad (años)",
            yaxis_title="Número de participaciones",
        )

        return fig

    @render_widget
    def grafico_oxigeno():
        # Si se eligió una montaña, se usan solo sus participaciones
        tabla = datos_filtrados()
        elegida = input.montana()
        if elegida != "Todas las montañas":
            tabla = tabla[tabla["peak_name"] == elegida]

        usos= [True, False]
        nombres= ["Con oxígeno", "Sin oxígeno"]
        textos=[]
        porcentajes=[]
        cantidades=[]

        #se recorren los dos grupos de uso de oxígeno
        for i in range(len(usos)):
             # Solo se cuentan participaciones con success conocido
            grupo = tabla[(tabla["oxygen_used"] == usos[i]) & (tabla["success"].notna())]
            n = len(grupo)
            cantidades.append(n)

            if n >= MIN_N:
                porcentaje = grupo["success"].sum() / n * 100
                porcentajes.append(porcentaje)
                textos.append(str(round(porcentaje, 1)) + " % (n = " + str(n) + ")")
            else:
                porcentajes.append(None)
                textos.append("")

        fig = go.FigureWidget(go.Bar(x=nombres, y=porcentajes, text=textos, textposition="outside"))

        # Se indican los grupos que tienen pocos datos
        for i in range(len(usos)):
            if cantidades[i] < MIN_N:
                fig.add_annotation(
                    x=nombres[i],
                    y=10,
                    text="pocos datos (n = " + str(cantidades[i]) + ")",
                    showarrow=False
                )

        fig.update_layout(
            title="Éxito según uso de oxígeno",
            yaxis_title="Porcentaje de éxito",
            yaxis=dict(range=[0, 110]),
        )
        return fig

    @render.ui
    def revision():
        tabla = datos_filtrados()
        elegida = input.montana()
        if elegida != "Todas las montañas":
            tabla = tabla[tabla["peak_name"] == elegida]

        n_total = len(tabla)
        edades_faltan = 0
        edades_revisar = 0
        n_edades = 0

        # Se recorren las edades para contar faltantes, edades raras y edades válidas
        for edad in tabla["age"]:
            if pd.isna(edad):
                edades_faltan = edades_faltan + 1
            elif edad < 15 or edad > 90:
                edades_revisar = edades_revisar + 1
            else:
                n_edades = n_edades + 1

        # Se cuentan las participaciones con dato de éxito
        sin_exito = 0
        for valor in tabla["success"]:
            if pd.isna(valor):
                sin_exito = sin_exito + 1

        # Solo cuentan las participaciones con éxito y uso de oxígeno conocidos
        n_exito = len(tabla[
            (tabla["success"].notna()) &
            (tabla["oxygen_used"].notna())
        ])
        sin_oxigeno = tabla["oxygen_used"].isna().sum()


        return ui.div(
            ui.p(
                "Estos números cambian con los filtros. Cada gráfico utiliza las participaciones que tienen los datos necesarios.",
                class_="small",
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Histograma de edades"),
                    ui.h2(str(n_edades)),
                    ui.p("Participaciones con edad entre 15 y 90 años", class_="small"),
                ),
                ui.card(
                    ui.card_header("Gráfico de oxígeno"),
                    ui.h2(str(n_exito)),
                    ui.p("Participaciones con dato de oxígeno y de éxito", class_="small"),
                ),
            ),
            ui.p(
                "Excluidas del histograma: " + str(edades_faltan) + " sin edad y "
                + str(edades_revisar) + " fuera de 15 a 90 años. "
                + "Excluidas de la comparación de oxígeno: " + str(sin_exito) + " sin dato de éxito y "
                + str(sin_oxigeno) + " sin dato de oxígeno.",
                class_="small",
            ),
        )

