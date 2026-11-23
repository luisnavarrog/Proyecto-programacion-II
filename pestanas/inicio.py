"""Portada y accesos a las exploraciones de la app."""
from shiny import ui


def panel_ui(expeditions, peaks):
    anios = expeditions["year"].dropna()
    periodo = f"{anios.min():.0f}–{anios.max():.0f}"
    cantidad_picos = f'{peaks["peak_id"].nunique():,}'.replace(",", "\u202f")
    cantidad_expediciones = f'{expeditions["expedition_id"].nunique():,}'.replace(",", "\u202f")

    return ui.div(
        ui.tags.section(
            ui.div(
                ui.h1("Expediciones al Himalaya", class_="display-4 fw-bold"),
                ui.p(
                    "Explora más de un siglo de expediciones. Compara montañas por "
                    "elevación y actividad, y descubre cómo varía el uso de oxígeno "
                    "según la temporada.",
                    class_="lead mb-0",
                ),
                class_="inicio-presentacion",
            ),
            class_="inicio-portada",
        ),
        ui.tags.dl(
            ui.div(ui.tags.dt("Período cubierto"), ui.tags.dd(periodo)),
            ui.div(ui.tags.dt("Picos catalogados"), ui.tags.dd(cantidad_picos)),
            ui.div(ui.tags.dt("Expediciones registradas"), ui.tags.dd(cantidad_expediciones)),
            class_="inicio-cifras",
        ),
        ui.h2("Explora los datos", class_="h4 mt-4"),
        ui.layout_columns(
            ui.card(
                ui.p(
                    "¿Cómo se acumularon las cumbres alcanzadas y las muertes en cada pico a lo largo del tiempo?",
                    class_="fw-semibold",
                ),
                ui.input_action_button(
                    "abrir_evolucion", "Ir a Evolución", class_="btn-outline-primary"
                ),
            ),
            ui.card(
                ui.p("¿Cuáles son las montañas más visitadas y a qué altitudes se concentran las expediciones?", class_="fw-semibold"),
                ui.input_action_button("abrir_picos", "Ir a Picos", class_="btn-outline-primary"),
            ),
            ui.card(
                ui.p("¿Qué edades predominan y cómo varía el éxito según el uso de oxígeno?", class_="fw-semibold"),
                ui.input_action_button(
                    "abrir_perfil", "Ir a Perfil y oxígeno", class_="btn-outline-primary"
                ),
            ),
            ui.card(
                ui.p(
                    "¿Cómo cambian la participación, el éxito, la mortalidad y el uso de oxígeno según el pico, la nacionalidad y el período?",
                    class_="fw-semibold",
                ),
                ui.input_action_button(
                    "abrir_calor", "Ir al Mapa de calor", class_="btn-outline-primary"
                ),
            ),
            col_widths={"sm": (12, 12, 12, 12), "md": (6, 6, 6, 6)},
        ),
        ui.p(
            "Fuente de datos: Himalayan Database, vía TidyTuesday.",
            class_="small text-body-secondary mt-4",
        ),
        class_="container-xl py-4",
    )
