"""Paleta compartida por los gráficos de Plotly."""

PANEL = "#142740"
TEXTO = "#F2F7FF"
CUADRICULA = "#304762"
GLACIAR = "#67DFE8"
COLORES_RANGOS = ("#A98BD2", "#55C1E1", "#E2A743", "#E47777")


def aplicar_tema(figura):
    figura.update_layout(
        template="plotly_dark",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(family="sans-serif", color=TEXTO),
        annotationdefaults=dict(font=dict(color=TEXTO)),
        hoverlabel=dict(bgcolor=PANEL, font=dict(color=TEXTO)),
    )
    figura.update_xaxes(
        gridcolor=CUADRICULA,
        zerolinecolor=CUADRICULA,
        linecolor=CUADRICULA,
        tickfont=dict(color=TEXTO),
        title_font=dict(color=TEXTO),
    )
    figura.update_yaxes(
        gridcolor=CUADRICULA,
        zerolinecolor=CUADRICULA,
        linecolor=CUADRICULA,
        tickfont=dict(color=TEXTO),
        title_font=dict(color=TEXTO),
    )
    return figura
