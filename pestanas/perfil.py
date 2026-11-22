"""Pestaña: Perfil y oxígeno."""

import pandas as pd
import plotly.graph_objects as go
from shiny import module, render, ui, reactive
from shinywidgets import output_widget, render_widget #con render muestro el grafico dentro de shiny

from src.datos import cargar_datos  #traigo la tabla de integrantes
from src.tema import GLACIAR, aplicar_tema

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
            ui.input_select("montana", "Montaña", opciones, selected="Todas"),
            ui.input_select("temporada",
                             "Temporada",
                             choices={"Todas":"Todas las temporadas", 
                                      "Spring": "Primavera",
                                        "Summer": "Verano",
                                          "Autumn": "Otoño", 
                                          "Winter": "Invierno"}, 
                                          selected="Todas las temporadas"),

            ui.input_slider("anio", "Años", min=anio_min, max=anio_max, value=(anio_min, anio_max), sep=""),
            ui.help_text("Seleccione una montaña, una temporada y un rango de años para visualizar los datos."),
            ui.help_text("Los porcentajes de éxito se muestran para grupos con al menos " + str(MIN_N) + " participaciones."),
        ),

        ui.card(
            ui.card_header("Perfil y oxígeno: edades y éxito"),
            ui.hr(),
            ui.h5("¿Cómo se distribuyen las edades registradas y cómo varía el éxito según el uso de oxígeno?", class_="mt-3 mb-3"),
            ui.hr(),
            
            ui.layout_columns(
                ui.div(
                    ui.h5("Distribución de edades", class_="text-white fw-bold"),
                    output_widget("grafico_edades"),
                    ui.hr(),
                    ui.output_ui("nota_edades")
                ),
                ui.div(
                    ui.h5("Éxito según uso de oxígeno", class_="text-white fw-bold"),
                    output_widget("grafico_oxigeno"),
                    ui.hr(),
                    ui.output_ui("nota_oxigeno")
                ),
                fill= False,
            ),
        
            ui.hr(),
            ui.output_ui("interpretacion"), #agregar intepretacion para que se vea mas completa la pestaña

            ui.hr(),
            ui.p("Las diferencias observadas son descriptivas y no permiten afirmar que el uso de oxígeno cause un mayor éxito.", class_="small text-white-50"),
        ),
    )


@module.server
def panel_server(input, output, session):
    members, _, _ = cargar_datos()

    @reactive.calc
    def datos_filtrados():
        #se filtra la tabla por el rango de años del slider
        rango = input.anio()
        tabla = members[(members["year"] >= rango[0]) & (members["year"] <= rango[1])]
    
        #si se elige solo una montaña, se usaran solos sus participantes
        elegida= input.montana()
        if elegida != "Todas las montañas":
            tabla= tabla[tabla["peak_name"]==elegida]

        #si se elige una temporada, se usaran solo sus participantes
        elegida_temporada= input.temporada()
        if elegida_temporada != "Todas":
            tabla= tabla[tabla["season"]==elegida_temporada]
        return tabla

    

    @render_widget
    def grafico_edades(): #guarda solo las edades válidas (escogí entre 15 y 90)
        tabla = datos_filtrados()
        edades=[]

        for edad in tabla["age"]:
            if pd.notna(edad) and edad >= 15 and edad <= 90: #verifica primero que no sea un valor nulo y luego que esté en el rango de 15 a 90
                edades.append(edad)

        # Histograma con intervalos de 5 años
        fig = go.FigureWidget(
            go.Histogram( 
                x=edades,
                xbins=dict(start=15, end=95, size=5),
                marker=dict(color=GLACIAR)
            )
        )

        fig.update_layout(
            xaxis_title="Edad (años)",
            yaxis_title="Número de participaciones",
            font= dict(color= "#FFFFFF"),
            height= 350,
            bargap=0.05, #espacio entre barras
            plot_bgcolor= "rgba(0,0,0,0)", #color de fondo del grafico
            paper_bgcolor= "rgba(0,0,0,0)",
            margin=dict(l=65, r=20, t=15, b=60) #margen izquierdo, derecho, superior e inferior (es el orden en que se colocan los valores)
        )


        fig.update_yaxes(gridcolor="rgba(255,255,255,0.15)") #crea líneas muy sutiles y tenues que sirven de guía visual sin saturar el gráfico
        fig.update_xaxes(showgrid=False) #oculto las líneas verticales del eje x para que no se vean
        aplicar_tema(fig)
        return fig
    

    @render_widget
    def grafico_oxigeno():
        # Si se eligió una montaña, se usan solo sus participaciones
        tabla = datos_filtrados()
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
                textos.append(str(round(porcentaje, 1)).replace(".", ",") + " % ")
            else:
                porcentajes.append(None)
                textos.append("")

        fig = go.FigureWidget(
            go.Bar(x=nombres,
                    y=porcentajes, 
                    text=textos, 
                    textposition="outside",
                    textfont=dict(size=16,color="#FFFFFF"),
                    marker_color= ["#509693", "#B9D9CB"],
                    width=0.40
                    ))

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
            yaxis_title="Porcentaje de éxito",
            yaxis=dict(range=[0, 110]),
            font= dict(color= "#FFFFFF"),
            height= 350,
            plot_bgcolor= "rgba(0,0,0,0)",
            paper_bgcolor= "rgba(0,0,0,0)",
            margin= dict(l=65, r=20, t=15, b=60)
        )

        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.15)",
            ticksuffix=" %") #añade el %
        fig.update_xaxes(
            showgrid=False,
            tickmode="array",
            tickvals=nombres, #categorias del eje x
            ticktext=[ #establece el texto que se mostrará en cada categoría del eje x
                "Con oxígeno<br>n = " + format(cantidades[0], ",").replace(",", "."),
                "Sin oxígeno<br>n = " + format(cantidades[1], ",").replace(",", ".")
            ]
        )
        aplicar_tema(fig)
        return fig

    @render.ui
    def nota_edades():
        tabla = datos_filtrados()
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

        return ui.div(
            ui.h2(format(n_edades, ",").replace(",", "."), class_="text-primary fw-bold"),
            ui.p("Participaciones con edades válidas (15-90 años).", class_="text-white"),
            ui.p(
                "Se excluyen: " + format(edades_faltan, ",").replace(",", ".")
                + " participaciones sin edad y "
                + format(edades_revisar, ",").replace(",", ".")
                + " fuera del intervalo.",
                class_="small text-white-50",
            ),
        )

    @render.ui
    def nota_oxigeno():
        tabla= datos_filtrados()
        #Cuento participantes con dato de exito y con/sin oxígeno
        sin_exito=0
        for valor in tabla["success"]:
            if pd.isna(valor):
                sin_exito += 1

        n_exito = len(tabla[
            (tabla["success"].notna()) &
            (tabla["oxygen_used"].notna())
        ])

        sin_oxigeno = tabla["oxygen_used"].isna().sum()

        if sin_exito == 0 and sin_oxigeno == 0:
            mensaje = ""
        else:
            mensaje = "Se excluyen " + str(sin_exito) + " participaciones sin dato de éxito y " + str(sin_oxigeno) + " sin dato de uso de oxígeno."

        return ui.div(
            ui.h2(format(n_exito, ",").replace(",", "."), class_="text-primary fw-bold"),
            ui.p("Participaciones con información sobre el resultado del ascenso y el uso de oxígeno.", class_="text-white"),
            ui.p(mensaje, class_="small text-white-50"),
        )
    @render.ui
    def interpretacion():
        tabla = datos_filtrados()

        # Éxito con y sin oxígeno, con el mismo cálculo del gráfico
        porcentajes = []
        cantidades = []
        for uso in [True, False]:
            grupo = tabla[(tabla["oxygen_used"] == uso) & (tabla["success"].notna())]
            n = len(grupo)
            cantidades.append(n)
            if n >= MIN_N:
                porcentajes.append(grupo["success"].sum() / n * 100)
            else:
                porcentajes.append(None)

        if cantidades[0] < MIN_N or cantidades[1] < MIN_N:
            texto_exito = "No hay suficientes participaciones en uno de los grupos para comparar el éxito."
        else:
            if porcentajes[0] > porcentajes[1]:
                texto_exito = (
                    "El porcentaje de éxito fue mayor entre las participaciones que utilizaron oxígeno, con un "
                    + str(round(porcentajes[0], 1)).replace(".", ",") + " %."
                )
            elif porcentajes[1] > porcentajes[0]:
                texto_exito = (
                    "El porcentaje de éxito fue mayor entre las participaciones que no utilizaron oxígeno, con un "
                    + str(round(porcentajes[1], 1)).replace(".", ",") + " %."
                )
            else:
                texto_exito = (
                    "Ambos grupos presentaron el mismo porcentaje de éxito ("
                    + str(round(porcentajes[0], 1)).replace(".", ",") + " %)."
                )

        # Rango de edad con más participaciones (intervalos de 5 años)
        edades = tabla["age"].dropna()
        edades = edades[(edades >= 15) & (edades <= 90)]
        if len(edades) > 0:
            grupos = pd.cut(edades, bins=list(range(15, 100, 5)), right=False)
            intervalo = grupos.value_counts().idxmax()
            texto_edad = (
                "El intervalo de "
                + str(int(intervalo.left)) + " a " + str(int(intervalo.right) - 1)
                + " años tiene la mayor cantidad de participaciones."

            )
        else:
            texto_edad = "No hay edades válidas para estos filtros."

        return ui.div(
            ui.h5("¿Qué muestran los datos?", class_="fw-bold"),
            ui.p(texto_edad, class_="text-white"),
            ui.p(texto_exito, class_="text-white"),
        )