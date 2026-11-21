"""Paleta compartida por los gráficos de Plotly."""

PANEL = "#142740"
TEXTO = "#F2F7FF"
CUADRICULA = "#304762"
GLACIAR = "#67DFE8"


def aplicar_tema(figura):
    figura.update_layout(
        template="plotly_dark",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXTO),
        hoverlabel=dict(bgcolor=PANEL, font=dict(color=TEXTO)),
    )
    figura.update_xaxes(gridcolor=CUADRICULA, zerolinecolor=CUADRICULA)
    figura.update_yaxes(gridcolor=CUADRICULA, zerolinecolor=CUADRICULA)
    return figura
