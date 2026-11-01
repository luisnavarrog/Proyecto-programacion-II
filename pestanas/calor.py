"""Pestaña: Mapa de calor."""
from shiny import module, ui


@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Mapa de calor"),
        ui.p("Pendiente: aquí va el mapa de calor."),
    )


@module.server
def panel_server(input, output, session, datos):
    pass
