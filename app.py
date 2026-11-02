"""App Shiny para el Himalayan Database (TidyTuesday 2020-09-22)."""
from shiny import App, ui, reactive
from src.datos import cargar_datos
from pestanas import evolucion, picos, perfil, calor

# Se carga una sola vez al iniciar la app
members, expeditions, peaks = cargar_datos()

temporadas = sorted(
    members.loc[members["season"] != "Unknown", "season"].dropna().unique()
)

app_ui = ui.page_sidebar(
    # Filtros globales: afectan a todas las pestañas
    ui.sidebar(
        ui.input_slider(
            "anios", "Rango de años",
            int(members["year"].min()), int(members["year"].max()),
            (int(members["year"].min()), int(members["year"].max())),
            sep="",
        ),
        ui.input_checkbox_group(
            "temporadas", "Temporada",
            choices=temporadas, selected=list(temporadas),
        ),
    ),
    ui.navset_tab(
        ui.nav_panel("Inicio", ui.p("Descripción del conjunto de datos y su contexto.")),
        ui.nav_panel("Evolución", evolucion.panel_ui("evolucion")),
        ui.nav_panel("Picos", picos.panel_ui("picos")),
        ui.nav_panel("Perfil y oxígeno", perfil.panel_ui("perfil")),
        ui.nav_panel("Mapa de calor", calor.panel_ui("calor")),
    ),
    title="Expediciones al Himalaya",
)


def server(input, output, session):
    @reactive.calc
    def datos():
        """members filtrado por los controles globales."""
        a, b = input.anios()
        d = members[members["year"].between(a, b)]
        return d[d["season"].isin(input.temporadas())]

    evolucion.panel_server("evolucion", datos=datos)
    picos.panel_server("picos", datos=datos)
    perfil.panel_server("perfil", datos=datos)
    calor.panel_server("calor", datos=datos)


app = App(app_ui, server)
