"""Pestaña: Evolución temporal."""
import pandas as pd
import plotly.express as px
from shiny import module
from shinywidgets import output_widget, render_widget


@module.ui
def panel_ui():
    return output_widget("grafico")


@module.server
def panel_server(input, output, session, expeditions: pd.DataFrame):
    @render_widget
    def grafico():
        counts = (
            expeditions.groupby("year")["expedition_id"]
            .nunique()
            .rename("expeditions")
            .reset_index()
        )
        return px.line(
            counts,
            x="year",
            y="expeditions",
            markers=True,
            labels={"year": "Año", "expeditions": "Cantidad de expediciones"},
            title="Expediciones a lo largo del tiempo",
            template="plotly_white",
            color_discrete_sequence=["#315C8C"],
        )
