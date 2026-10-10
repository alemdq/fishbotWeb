"""Clima y olas desde Open-Meteo (2 consultas por corrida, con caché de respaldo)."""
import datetime as dt
import json
import logging
import time
from pathlib import Path

import requests

from . import config as C

log = logging.getLogger(__name__)

VARIABLES_CLIMA = [
    "temperature_2m", "weather_code", "precipitation_probability", "precipitation",
    "rain", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "is_day",
]
VARIABLES_MAR = ["wave_height", "wave_direction", "wave_period"]


def _pedir(url, params, intentos=2):
    for n in range(intentos):
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if data.get("error"):
                raise ValueError(data.get("reason"))
            return data
        except Exception as e:  # noqa: BLE001
            log.warning("Open-Meteo falló (%s), intento %d: %s", url, n + 1, e)
            time.sleep(3)
    return None


def _con_cache(nombre, url, params, carpeta: Path):
    """Pide los datos; si falla, devuelve la última respuesta buena guardada."""
    archivo = carpeta / f"{nombre}.json"
    data = _pedir(url, params)
    if data:
        data["_obtenido"] = dt.datetime.now(C.TZ).isoformat(timespec="minutes")
        archivo.write_text(json.dumps(data, separators=(",", ":")))
        return data, True
    if archivo.exists():
        try:
            return json.loads(archivo.read_text()), False
        except (OSError, ValueError):
            pass
    return None, False


def clima(carpeta: Path):
    return _con_cache("clima", C.OPEN_METEO_CLIMA, {
        "latitude": C.LAT, "longitude": C.LON,
        "hourly": ",".join(VARIABLES_CLIMA),
        "daily": "sunrise,sunset",
        "wind_speed_unit": "kmh",
        "forecast_days": C.DIAS + 1,
        "timezone": C.TZ_NAME,
    }, carpeta)


def olas(carpeta: Path):
    return _con_cache("olas", C.OPEN_METEO_MAR, {
        "latitude": C.LAT, "longitude": C.LON,
        "hourly": ",".join(VARIABLES_MAR),
        "forecast_days": C.DIAS + 1,
        "timezone": C.TZ_NAME,
    }, carpeta)


def por_hora(data):
    """{'2026-10-10T06:00': {'temperature_2m': .., ...}} para buscar rápido."""
    if not data:
        return {}
    h = data.get("hourly", {})
    tiempos = h.get("time", [])
    claves = [k for k in h if k != "time"]
    return {t: {k: (h[k][i] if i < len(h[k]) else None) for k in claves} for i, t in enumerate(tiempos)}


def sol_por_dia(data):
    """{'2026-10-10': {'sale': '06:09', 'pone': '19:04'}}."""
    out = {}
    if not data or "daily" not in data:
        return out
    d = data["daily"]
    for i, fecha in enumerate(d.get("time", [])):
        try:
            out[fecha] = {"sale": d["sunrise"][i].split("T")[1], "pone": d["sunset"][i].split("T")[1]}
        except (KeyError, IndexError, AttributeError):
            pass
    return out
