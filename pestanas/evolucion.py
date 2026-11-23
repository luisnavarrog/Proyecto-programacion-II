"""Pestaña: evolución acumulada de las expediciones."""
import math

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import module, render, ui
from src.tema import COLORES_RANGOS, CUADRICULA, GLACIAR, PANEL, TEXTO, aplicar_tema


_PROFILE_X = (0, 0.12, 0.22, 0.34, 0.45, 0.56, 0.68, 0.79, 0.9, 1, 0)
_PROFILE_SHAPES = (
    (0, 0.22, 0.14, 0.44, 0.31, 0.78, 0.53, 1, 0.58, 0, 0),
    (0, 0.16, 0.37, 0.23, 0.66, 0.47, 0.94, 0.72, 0.51, 0, 0),
    (0, 0.33, 0.19, 0.59, 0.35, 0.87, 0.56, 1, 0.42, 0, 0),
)
_COLORS = (*COLORES_RANGOS, GLACIAR)


def _top_peaks(expeditions: pd.DataFrame) -> pd.DataFrame:
    data = expeditions.copy()
    data["participants"] = data[["members", "hired_staff"]].fillna(0).sum(axis=1)
    successful = data["termination_reason"].fillna("").str.startswith("Success")
    data["successful_participations"] = data["participants"].where(successful, 0)
    data["deaths"] = data[["member_deaths", "hired_staff_deaths"]].fillna(0).sum(
        axis=1
    )
    return (
        data.groupby(["peak_id", "peak_name"], as_index=False)
        .agg(
            successful_participations=("successful_participations", "sum"),
            expeditions=("expedition_id", "nunique"),
            deaths=("deaths", "sum"),
        )
        .sort_values(
            ["successful_participations", "peak_id"],
            ascending=[False, True],
        )
        .head(10)
        .reset_index(drop=True)
    )


def _cumulative_counts(
    expeditions: pd.DataFrame,
    peak_ids: list[str],
    years: list[int],
) -> pd.DataFrame:
    data = expeditions.dropna(subset=["year"]).copy()
    data = data.loc[data["peak_id"].isin(peak_ids)]
    data["year"] = data["year"].astype(int)
    data["participants"] = data[["members", "hired_staff"]].fillna(0).sum(axis=1)
    successful = data["termination_reason"].fillna("").str.startswith("Success")
    data["successful_participations"] = data["participants"].where(successful, 0)
    data["deaths"] = data[["member_deaths", "hired_staff_deaths"]].fillna(0).sum(
        axis=1
    )

    increments = data.groupby(["year", "peak_id"]).agg(
        successful_participations=("successful_participations", "sum"),
        deaths=("deaths", "sum"),
    )
    full_index = pd.MultiIndex.from_product(
        [years, peak_ids], names=["year", "peak_id"]
    )
    increments = increments.reindex(full_index, fill_value=0).sort_index()
    return increments.groupby(level="peak_id").cumsum()


def _mountain_trace(
    peak_name: str,
    position: int,
    value: int,
    successful_participations: int,
    deaths: int,
    year: int,
    color: str,
    shape_index: int,
    metric_label: str,
) -> go.Scatter:
    width = 0.78
    heights = _PROFILE_SHAPES[shape_index % len(_PROFILE_SHAPES)]
    x_values = [position + (ratio - 0.5) * width for ratio in _PROFILE_X]
    y_values = [value * ratio for ratio in heights]
    customdata = [
        [peak_name, year, successful_participations, deaths]
        for _ in x_values
    ]
    return go.Scatter(
        x=x_values,
        y=y_values,
        customdata=customdata,
        mode="lines",
        fill="toself",
        fillcolor=color,
        line={"color": color, "width": 1.5},
        opacity=0.86,
        hoveron="fills",
        name=peak_name,
        showlegend=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Acumulado hasta %{customdata[1]}:<br>"
            "Participaciones exitosas: %{customdata[2]:,.0f}<br>"
            "Personas fallecidas: %{customdata[3]:,.0f}<br>"
            f"{metric_label}: %{{y:,.0f}}<extra></extra>"
        ),
    )


def _animated_mountain_figure(
    summary: pd.DataFrame,
    cumulative: pd.DataFrame,
    years: list[int],
    year_initial: int,
    successful_max: int,
    deaths_max: int,
) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.16,
        subplot_titles=(
            "Participaciones exitosas acumuladas",
            "💀 Personas fallecidas acumuladas",
        ),
    )
    positions = list(range(len(summary)))

    def traces_for_year(year: int) -> list[go.Scatter]:
        current = cumulative.loc[year]
        traces = []
        for position, peak in summary.iterrows():
            counts = current.loc[peak["peak_id"]]
            successful = int(counts["successful_participations"])
            deaths = int(counts["deaths"])
            for metric, value, metric_label in (
                (
                    "successful_participations",
                    successful,
                    "Participaciones exitosas",
                ),
                ("deaths", deaths, "Personas fallecidas"),
            ):
                traces.append(
                    _mountain_trace(
                        peak_name=peak["peak_name"],
                        position=position,
                        value=value,
                        successful_participations=successful,
                        deaths=deaths,
                        year=year,
                        color=_COLORS[position % len(_COLORS)],
                        shape_index=position,
                        metric_label=metric_label,
                    )
                )
        return traces

    initial_traces = traces_for_year(year_initial)
    for position in range(len(summary)):
        fig.add_trace(initial_traces[position * 2], row=1, col=1)
        fig.add_trace(initial_traces[position * 2 + 1], row=2, col=1)

    frame_traces = list(range(len(initial_traces)))
    fig.frames = [
        go.Frame(
            name=str(year),
            data=[
                go.Scatter(y=trace.y, customdata=trace.customdata)
                for trace in traces_for_year(year)
            ],
            traces=frame_traces,
            layout={"title": {"text": f"Año: {year}"}},
        )
        for year in years
    ]

    steps = [
        {
            "label": str(year),
            "method": "animate",
            "args": [
                [str(year)],
                {
                    "mode": "immediate",
                    "frame": {"duration": 500, "redraw": True},
                    "transition": {"duration": 0},
                },
            ],
        }
        for year in years
    ]
    fig.update_layout(
        title={"text": f"Año: {year_initial}", "x": 0.5},
        height=950,
        hovermode="closest",
        showlegend=False,
        margin={"t": 110, "r": 30, "b": 120, "l": 70},
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0,
                "y": -0.15,
                "bgcolor": PANEL,
                "bordercolor": CUADRICULA,
                "font": {"color": TEXTO},
                "buttons": [
                    {
                        "label": "Reproducir",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "fromcurrent": True,
                                "frame": {"duration": 500, "redraw": True},
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "Pausar",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "mode": "immediate",
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": years.index(year_initial),
                "currentvalue": {
                    "prefix": "Año: ",
                    "font": {"color": TEXTO},
                },
                "steps": steps,
                "x": 0.12,
                "y": -0.15,
                "len": 0.88,
                "bgcolor": CUADRICULA,
                "activebgcolor": GLACIAR,
                "bordercolor": CUADRICULA,
                "font": {"color": TEXTO},
            }
        ],
    )
    fig.update_xaxes(
        range=[-0.5, len(summary) - 0.5],
        tickmode="array",
        tickvals=positions,
        ticktext=summary["peak_name"].tolist(),
        tickangle=-25,
        title=None,
        showgrid=False,
        zeroline=False,
        automargin=True,
        row=2,
        col=1,
    )
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_yaxes(
        title="Participaciones exitosas",
        range=[0, successful_max],
        tickformat=",.0f",
        zeroline=False,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title="Personas fallecidas",
        range=[0, deaths_max],
        tickformat=",.0f",
        zeroline=False,
        row=2,
        col=1,
    )
    return aplicar_tema(fig)


@module.ui
def panel_ui():
    return ui.div(
        ui.h2("¿Cómo cambió la cantidad de expediciones a lo largo del tiempo?"),
        ui.card(
            ui.card_header("Top 10 picos"),
            ui.p("Análisis estadístico por pico"),
            ui.output_ui("resumen_picos"),
        ),
        ui.card(
            ui.card_header("Evolución acumulada por pico"),
            ui.p("Cumbres alcanzadas y vidas perdidas a lo largo de la historia."),
            ui.output_ui("animacion"),
        ),
    )


@module.server
def panel_server(input, output, session, expeditions: pd.DataFrame):
    summary = _top_peaks(expeditions)
    peak_ids = summary["peak_id"].tolist()
    year_max = int(expeditions["year"].max())
    year_min = int(expeditions["year"].min())
    years = list(range(year_min, year_max + 1))
    cumulative = _cumulative_counts(expeditions, peak_ids, years)
    visible_threshold = summary["successful_participations"].max() * 0.05
    year_initial = next(
        year
        for year in years
        if cumulative.loc[year, "successful_participations"].max()
        >= visible_threshold
    )
    animation_years = years[years.index(year_initial) :]
    successful_max = max(
        1, math.ceil(summary["successful_participations"].max() * 1.1)
    )
    deaths_max = max(1, math.ceil(summary["deaths"].max() * 1.1))
    plotly_js_included = False

    @render.ui
    def resumen_picos():
        columns = (
            ("peak_id", "Código"),
            ("peak_name", "Pico"),
            ("successful_participations", "Participaciones exitosas"),
            ("expeditions", "Expediciones"),
            ("deaths", "Fallecidos"),
        )
        return ui.tags.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(*[ui.tags.th(label) for _, label in columns])
                ),
                ui.tags.tbody(
                    *[
                        ui.tags.tr(
                            *[
                                ui.tags.td(
                                    f"{int(peak[column]):,}"
                                    if column
                                    in {
                                        "successful_participations",
                                        "expeditions",
                                        "deaths",
                                    }
                                    else peak[column]
                                )
                                for column, _ in columns
                            ]
                        )
                        for _, peak in summary.iterrows()
                    ]
                ),
                class_="table table-striped table-sm",
            ),
            class_="table-responsive",
        )

    @render.ui
    def animacion():
        nonlocal plotly_js_included
        figure = _animated_mountain_figure(
            summary,
            cumulative,
            animation_years,
            year_initial,
            successful_max,
            deaths_max,
        )
        html = figure.to_html(
            full_html=False,
            include_plotlyjs=not plotly_js_included,
            auto_play=False,
            config={"responsive": True, "displaylogo": False},
        )
        plotly_js_included = True
        return ui.HTML(html)