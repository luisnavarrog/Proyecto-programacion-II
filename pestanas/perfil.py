"""Pestaña: Perfil y oxígeno."""
import pandas as pd
import plotly.graph_objects as go
from shiny import module, render, ui
from shinywidgets import output_widget, render_widget #con render muestro el grafico dentro de shiny

from src.datos import cargar_datos  #traigo la tabla de integrantes

#Menos de 20 integrantes, no se mostrara el porcentaje
MIN_N = 20


@module.ui
def panel_ui():
    #leer las 20 montañas con mas integrantes para seleccionar ese sector
    members, _, _ = cargar_datos()  #llamo a la funcion cargar_datos para traer la tabla de integrantes
    top= members["peak_name"].value_counts().head(20).index.tolist()  #selecciono las 20 montañas con mas integrantes
    opciones= ["Todas las montañas"] + top  #agrego la opcion de todas las montañas


    return ui.card(
        ui.card_header("Pregunta 3: edades y éxito según oxígeno"),
        ui.p("¿Cómo se distribuyen las edades registradas y cómo varía el éxito según el uso de oxígeno?"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Distribución de edades"),
                output_widget("grafico_edades"),
            ),
            ui.card(
                ui.card_header("Éxito según uso de oxígeno"),
                ui.input_select("montana", "Montaña", opciones, selected="Todas las montañas"),
                output_widget("grafico_oxigeno"),
            ),

        ),
        ui.card(
            ui.card_header("Revisión de edades y faltantes"),
            ui.output_text("resumen"),
        ),
         ui.p("Comparación descriptiva: las diferencias pueden relacionarse con la montaña, la temporada y el período. No demuestra un efecto causal del oxígeno."),

    )


@module.server
def panel_server(input, output, session):
    members, _, _ = cargar_datos()

    @render_widget
    def grafico_edades(): #guarda solo las edades válidas (se escogio entre 15 y 90)
        edades=[]
        for edad in members["age"]:
            if edad >= 15 and edad <= 90:
                edades.append(edad)

        # Histograma con intervalos de 5 años
        fig = go.FigureWidget(go.Histogram(x=edades, xbins=dict(start=15, end=90, size=5)))
        fig.update_layout(
            title="Distribución de edades",
            xaxis_title="Edad (años)",
            yaxis_title="Número de integrantes",
        )
        return fig
    
