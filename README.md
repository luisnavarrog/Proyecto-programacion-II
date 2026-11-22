# Expediciones al Himalaya

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Shiny](https://img.shields.io/badge/Shiny_for_Python-App-007BC2?logo=posit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Visualización-3F4F75?logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Datos-150458?logo=pandas&logoColor=white)

Aplicación web interactiva desarrollada en **Shiny for Python** para explorar el registro histórico de integrantes, expediciones y cumbres del **Himalayan Database** (*TidyTuesday 2020-09-22*).

![Portada Everest](www/imagenes/everest-portada.webp)

## Pestañas y funcionalidades

La interfaz utiliza un tema oscuro personalizado (`shinyswatch` *darkly* + CSS propio) y está organizada en cinco módulos dentro de `pestanas/`:

- **Inicio (`inicio.py`):** Portada del proyecto, métricas globales de expediciones y cumbres, y accesos directos hacia las vistas principales.
- **Picos (`picos.py`):** Exploración individual de montañas del Himalaya con siluetas vectoriales `.svg` procesadas dinámicamente (máscaras de desvanecimiento y escala comparativa de altitud sobre una base de 9.000 m).
- **Mapa de calor (`calor.py`):** Matriz interactiva en Plotly que analiza registros desde **1950 en adelante**, permitiendo cruzar:
  - **Indicadores:** Tasa de éxito (%), tasa de mortalidad (%), uso de oxígeno (%) y número de integrantes.
  - **Agrupación:** Top 5, 10 o 20 **picos** o **nacionalidades** con mayor participación.
  - **Período:** **Década** o **estación del año** (Primavera, Verano, Otoño, Invierno).
  - *Nota metodológica:* Las celdas con menos de **5 integrantes** se ocultan al calcular tasas para evitar distorsiones por tamaño de muestra reducido.
- **Evolución (`evolucion.py`):** *(En desarrollo)* Estructura de interfaz preparada para el análisis histórico temporal.
- **Perfil y oxígeno (`perfil.py`):** *(En desarrollo)* Estructura de interfaz preparada para el análisis demográfico y uso de oxígeno suplementario.

## Conjuntos de datos

Los archivos CSV se almacenan localmente en `data/` y se cargan una única vez al iniciar la aplicación mediante caché en memoria (`src/datos.py`):

| Archivo | Contenido | Tamaño aprox. |
| :--- | :--- | :--- |
| `data/peaks.csv` | Catálogo de cumbres, elevación, ubicación y estado de ascenso | ~29 KB |
| `data/expeditions.csv` | Historial de expediciones, rutas, temporadas y resultados | ~1.37 MB |
| `data/members.csv` | Registro individual de integrantes, nacionalidad, uso de oxígeno y desenlace | ~9.34 MB |

## Estructura del proyecto

```text
Proyecto-programacion-II/
├── app.py                  # Configuración de interfaz, navegación y servidor Shiny
├── requirements.txt        # Dependencias del proyecto
├── data/                   # Bases de datos del Himalayan Database
│   ├── expeditions.csv
│   ├── members.csv
│   └── peaks.csv
├── pestanas/               # Módulos UI y Server de cada pestaña
│   ├── __init__.py
│   ├── inicio.py
│   ├── picos.py
│   ├── calor.py
│   ├── evolucion.py
│   └── perfil.py
├── src/                    # Lógica auxiliar, caché de datos, SVG y estilos de gráficos
│   ├── __init__.py
│   ├── datos.py
│   ├── ilustraciones.py
│   └── tema.py
└── www/                    # Recursos estáticos servidos por Shiny
    ├── tema.css
    └── imagenes/
        ├── everest-portada.webp
        └── *.svg           # Siluetas vectoriales de los picos
```

## Requisitos e instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/luisnavarrog/Proyecto-programacion-II.git
   cd Proyecto-programacion-II
   ```

2. **Crear y activar un entorno virtual (opcional, recomendado):**

   ```powershell
   python -m venv .venv
   # En Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # En Linux / macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**

   ```powershell
   python -m pip install -r requirements.txt
   ```

## Ejecución

Desde la carpeta raíz del proyecto, inicia el servidor local de Shiny:

```powershell
python -m shiny run --reload app.py
```

Luego abre en tu navegador la URL local que muestra la consola (por defecto `http://127.0.0.1:8000`).

## Autores

- **Luis Navarro** ([@luisnavarrog](https://github.com/luisnavarrog)) y equipo del curso *Programación II*.