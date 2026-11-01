"""Carga de los tres CSV desde la carpeta data/."""
from functools import lru_cache
from pathlib import Path

import pandas as pd


CARPETA = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def cargar_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devuelve los datos de integrantes, expediciones y picos."""
    members = pd.read_csv(CARPETA / "members.csv")
    expeditions = pd.read_csv(CARPETA / "expeditions.csv")
    peaks = pd.read_csv(CARPETA / "peaks.csv")
    return members, expeditions, peaks
