# Expediciones al Himalaya

Aplicación interactiva en Shiny para explorar los datos de integrantes,
expediciones y picos del Himalayan Database.

## Estructura

- `app.py`: interfaz, filtros globales y conexión de las pestañas.
- `src/datos.py`: carga los archivos CSV una sola vez al iniciar.
- `pestanas/`: interfaz y lógica de servidor de cada pestaña.
- `data/`: `members.csv`, `expeditions.csv` y `peaks.csv`.

## Ejecución

Desde la carpeta del proyecto, instala las dependencias y ejecuta:

```powershell
python -m pip install -r requirements.txt
python -m shiny run --reload app.py
```

Las pestañas están preparadas; sus gráficos se incorporarán en sus respectivos
módulos dentro de `pestanas/`.