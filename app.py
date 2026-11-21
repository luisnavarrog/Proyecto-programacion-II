"""App Shiny para el Himalayan Database (TidyTuesday 2020-09-22)."""
from shiny import App, reactive, ui
from src.datos import cargar_datos
from pestanas import evolucion, picos, perfil, calor, inicio
from pathlib import Path
import shinyswatch

# Se carga una sola vez al iniciar la app
members, expeditions, peaks = cargar_datos()

app_ui = ui.page_fluid(
    ui.tags.head(ui.tags.link(rel="stylesheet", href="tema.css")),
    ui.navset_tab(
        ui.nav_panel("Inicio", inicio.panel_ui(expeditions, peaks)),
        ui.nav_panel("Evolución", evolucion.panel_ui("evolucion")),
        ui.nav_panel("Picos", picos.panel_ui("picos"), value="picos"),
        ui.nav_panel("Perfil y oxígeno", perfil.panel_ui("perfil")),
        ui.nav_panel("Mapa de calor", calor.panel_ui("calor"), value="calor"),
        id="pestanas",
    ),
    title="Expediciones al Himalaya",
    theme=shinyswatch.theme.darkly(),
)


def server(input, output, session):
    calor.panel_server("calor")
    picos.panel_server("picos")

    @reactive.effect
    @reactive.event(input.abrir_picos)
    def abrir_picos():
        ui.update_navs("pestanas", selected="picos")

    @reactive.effect
    @reactive.event(input.abrir_calor)
    def abrir_calor():
        ui.update_navs("pestanas", selected="calor")


app = App(
    app_ui,
    server,
    static_assets=Path(__file__).resolve().parent / "www",
)
