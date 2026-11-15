"""Pestaña: Picos."""
from shiny import module, ui


@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Picos"),
        ui.p("Pendiente: aquí va el análisis de los picos."),
    )
