"""Pestaña: Perfil y oxígeno."""
from shiny import module, ui


@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Perfil y oxígeno"),
        ui.p("Pendiente: aquí va el análisis del perfil de los integrantes."),
    )


@module.server
def panel_server(input, output, session, datos):
    pass
