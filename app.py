from shiny import App, ui, render

# 1. Interfaz de Usuario (UI)
app_ui = ui.page_fluid(
    ui.h2("¡Hola, Shiny para Python!"),
    ui.input_slider("n", "Elige un número:", 0, 100, 20),
    ui.output_text_verbatim("txt"),
)

# 2. Lógica del Servidor
def server(input, output, session):
    @output
    @render.text
    def txt():
        return f"El valor seleccionado es {input.n()}"

# 3. Crear la aplicación
app = App(app_ui, server)