"""Carga y presentación de las ilustraciones de la pestaña Picos."""
from pathlib import Path
import xml.etree.ElementTree as ET

from shiny import ui


# Agregar estos archivos a www/imagenes activa cada ilustración
archivos_picos = {
    "EVER": "everest.svg",
    "AMAD": "ama_dablam.svg",
    "CHOY": "cho_oyu.svg",
    "MANA": "manaslu.svg",
    "LHOT": "lhotse.svg",
    "DHA1": "dhaulagiri_i.svg",
    "MAKA": "makalu.svg",
    "BARU": "baruntse.svg",
    "PUMO": "pumori.svg",
    "ANN1": "annapurna_i.svg",
    "KANG": "kangchenjunga.svg",
    "HIML": "himlung_himal.svg",
    "ANN4": "annapurna_iv.svg",
    "PUTH": "putha_hiunchuli.svg",
    "TILI": "tilicho.svg",
    "NUPT": "nuptse.svg",
    "TUKU": "tukuche.svg",
    "JANU": "jannu.svg",
    "LANG": "langtang_lirung.svg",
    "MAK2": "makalu_ii.svg",
    "ANN3": "annapurna_iii.svg",
    "ANNS": "annapurna_south.svg",
    "LSHR": "lhotse_shar.svg",
    "ANN2": "annapurna_ii.svg",
    "GAUR": "gaurishankar.svg",
    "KGUR": "kang_guru.svg",
    "DORJ": "dorje_lhakpa.svg",
    "GANG": "gangapurna.svg",
    "KTEG": "kangtega.svg",
    "TAWO": "tawoche.svg",
}
carpeta_imagenes = Path(__file__).resolve().parent.parent / "www" / "imagenes"


def preparar_ilustracion(identificador, nombre, altura, elevacion_comparada=None):
    """Devuelve el SVG del pico o su respaldo con el encuadre de la ficha."""
    archivo_svg = carpeta_imagenes / archivos_picos.get(
        identificador, "generica.svg"
    )
    es_generica = False
    if not archivo_svg.is_file():
        archivo_svg = carpeta_imagenes / "generica.svg"
    if archivo_svg.name == "generica.svg":
        es_generica = True

    ilustracion = ui.p("Ilustración en preparación.")
    if archivo_svg.is_file():
        # Acercar el encuadre a la cima sin modificar el archivo original
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        dibujo = ET.fromstring(archivo_svg.read_text(encoding="utf-8"))
        dibujo.set("viewBox", "45 0 590 335")
        if elevacion_comparada is not None:
            dibujo.set("viewBox", "0 0 800 450")
        dibujo.set("width", "100%")
        dibujo.set("role", "img")
        dibujo.set("aria-label", f"{nombre}, {altura}. Silueta ilustrativa.")

        # Desvanecer los laterales y la base sobre el fondo de la ficha
        efectos = ET.fromstring("""
            <defs xmlns="http://www.w3.org/2000/svg">
                <linearGradient id="picos-laterales" x1="0" x2="1" y1="0" y2="0">
                    <stop offset="0%" stop-color="black"/>
                    <stop offset="7%" stop-color="white"/>
                    <stop offset="93%" stop-color="white"/>
                    <stop offset="100%" stop-color="black"/>
                </linearGradient>
                <linearGradient id="picos-base" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stop-color="white"/>
                    <stop offset="73%" stop-color="white"/>
                    <stop offset="100%" stop-color="black"/>
                </linearGradient>
                <mask id="picos-mascara-lateral" maskUnits="userSpaceOnUse"
                      x="45" y="0" width="590" height="335"
                      mask-type="luminance">
                    <rect x="45" y="0" width="590" height="335"
                          fill="url(#picos-laterales)"/>
                </mask>
                <mask id="picos-mascara-base" maskUnits="userSpaceOnUse"
                      x="45" y="0" width="590" height="335"
                      mask-type="luminance">
                    <rect x="45" y="0" width="590" height="335"
                          fill="url(#picos-base)"/>
                </mask>
            </defs>
        """)
        paisaje = ET.Element(
            "{http://www.w3.org/2000/svg}g",
            {"mask": "url(#picos-mascara-base)"},
        )
        for parte in list(dibujo):
            dibujo.remove(parte)
            paisaje.append(parte)

        if elevacion_comparada is not None:
            # La cima original está en y=61 y la base en y=410
            # Una elevación de 9000 m ocupa 349 unidades verticales
            factor = elevacion_comparada / 9000
            paisaje.set(
                "transform",
                f"translate(364 410) scale({factor}) translate(-364 -410)",
            )
            # Conservar la figura completa para comparar desde una misma base
            paisaje.attrib.pop("mask", None)
            for elemento in efectos.iter():
                if elemento.tag.endswith("mask") or elemento.tag.endswith("rect"):
                    elemento.set("x", "0")
                    elemento.set("y", "0")
                    elemento.set("width", "800")
                    elemento.set("height", "450")

        laterales = ET.Element(
            "{http://www.w3.org/2000/svg}g",
            {"mask": "url(#picos-mascara-lateral)"},
        )
        laterales.append(paisaje)
        dibujo.append(efectos)
        dibujo.append(laterales)

        if elevacion_comparada is not None:
            linea_base = ET.SubElement(
                dibujo,
                "{http://www.w3.org/2000/svg}path",
                {"d": "M0 410 H800", "stroke": "#b7c9d7", "stroke-width": "1"},
            )

        # Mostrar la elevación por encima de la cima
        etiqueta = ET.SubElement(
            dibujo,
            "{http://www.w3.org/2000/svg}text",
            {
                "x": "364",
                "y": "37",
                "text-anchor": "middle",
                "font-family": "sans-serif",
                "font-size": "19",
                "font-weight": "bold",
                "fill": "#24445f",
            },
        )
        if elevacion_comparada is not None:
            etiqueta.set("y", str(410 - 349 * factor - 24))
        etiqueta.text = altura
        # Cada ficha necesita identificadores propios para sus máscaras
        nombres_svg = {}
        for elemento in dibujo.iter():
            nombre = elemento.get("id")
            if nombre:
                nombres_svg[nombre] = f"pico-{identificador}-{nombre}"
                elemento.set("id", nombres_svg[nombre])
        for elemento in dibujo.iter():
            for atributo, valor in list(elemento.attrib.items()):
                for anterior, nuevo in nombres_svg.items():
                    valor = valor.replace(f"url(#{anterior})", f"url(#{nuevo})")
                    if atributo.endswith("href") and valor == f"#{anterior}":
                        valor = f"#{nuevo}"
                elemento.set(atributo, valor)
        contenido_svg = ET.tostring(dibujo, encoding="unicode")
        ilustracion = ui.div(ui.HTML(contenido_svg))
        if es_generica:
            ilustracion = ui.div(
                ilustracion,
                ui.p("Ilustración genérica.", class_="small text-muted"),
            )

    return ilustracion
