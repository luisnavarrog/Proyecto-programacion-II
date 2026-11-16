"""Pestaña: Picos."""
from shiny import module, ui, render
from src.datos import cargar_datos
members, expeditions, peaks = cargar_datos()

# Contar las expediciones registradas por montaña
conteo_picos = expeditions.groupby(["peak_id", "peak_name"]).size()
conteo_picos = conteo_picos.reset_index(name="cantidad")

# Ordenar las montañas de mayor a menor cantidad de expediciones
conteo_picos = conteo_picos.sort_values("cantidad", ascending=False)

# Seleccionar las diez montañas con más expediciones
top_picos = conteo_picos.head(10)



@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Picos"),
        ui.output_table("tabla_picos"),
    )



@module.server
def panel_server(input, output, session):

    @render.table
    def tabla_picos():
        return top_picos