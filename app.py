"""App Shiny para el Himalayan Database (TidyTuesday 2020-09-22)."""
from shiny import App, ui
from src.datos import cargar_datos
from pestanas import evolucion, picos, perfil, calor
from pathlib import Path
import shinyswatch 

# Se carga una sola vez al iniciar la app
members, expeditions, peaks = cargar_datos()

app_ui = ui.page_fluid(
    ui.navset_tab(
        ui.nav_panel("Inicio", ui.p("Descripción del conjunto de datos y su contexto.")),
        ui.nav_panel("Evolución", evolucion.panel_ui("evolucion")),
        ui.nav_panel("Picos", picos.panel_ui("picos")),
        ui.nav_panel("Perfil y oxígeno", perfil.panel_ui("perfil")),
        ui.nav_panel("Mapa de calor", calor.panel_ui("calor")),
    ),
    title="Expediciones al Himalaya",
    theme=shinyswatch.theme.solar(),
)


def server(input, output, session):
    calor.panel_server("calor")
    picos.panel_server("picos")

app = App(
    app_ui,
    server,
    static_assets=Path(__file__).resolve().parent / "www",
)
