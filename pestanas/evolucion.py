"""Pestaña: Evolución temporal."""
from shiny import module, ui


@module.ui
def panel_ui():
    return ui.card(
        ui.card_header("Evolución temporal"),
        ui.p("Pendiente: aquí va el gráfico."),
    )


@module.server
def panel_server(input, output, session, datos):
    pass
