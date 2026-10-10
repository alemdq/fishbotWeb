"""Períodos de pique (solunares), calculados con la posición de la luna.

Se calculan como en tablademareas:
- Períodos menores (1 h): salida y puesta de la luna, ± 30 min.
- Períodos mayores (2 h): luna arriba (punto medio entre salida y puesta) y
  luna abajo (punto medio entre puesta y la salida siguiente), ± 1 h.
"""
import datetime as dt

import ephem

from . import config as C


def _a_local(fecha_ephem):
    return ephem.Date(fecha_ephem).datetime().replace(tzinfo=dt.timezone.utc).astimezone(C.TZ)


def eventos_luna(desde, hasta):
    """Salidas y puestas de la luna entre dos datetimes con zona horaria."""
    obs = ephem.Observer()
    obs.lat = str(C.LAT)
    obs.lon = str(C.LON)
    obs.elevation = 0
    luna = ephem.Moon()
    eventos = []
    for tipo, fn in (("sale", obs.next_rising), ("pone", obs.next_setting)):
        obs.date = ephem.Date(desde.astimezone(dt.timezone.utc))
        while True:
            t = _a_local(fn(luna))
            if t > hasta:
                break
            eventos.append({"tipo": tipo, "dt": t})
            obs.date = ephem.Date(t.astimezone(dt.timezone.utc) + dt.timedelta(minutes=1))
    eventos.sort(key=lambda e: e["dt"])
    return eventos


def periodos(desde, hasta):
    """Lista de períodos de pique que tocan el rango [desde, hasta]."""
    margen = dt.timedelta(days=1)
    ev = eventos_luna(desde - margen, hasta + margen)
    out = []
    for e in ev:
        out.append({
            "tipo": "menor",
            "motivo": "Salida de la luna" if e["tipo"] == "sale" else "Puesta de la luna",
            "desde_dt": e["dt"] - dt.timedelta(minutes=30),
            "hasta_dt": e["dt"] + dt.timedelta(minutes=30),
        })
    for a, b in zip(ev, ev[1:]):
        if a["tipo"] == b["tipo"]:
            continue
        centro = a["dt"] + (b["dt"] - a["dt"]) / 2
        out.append({
            "tipo": "mayor",
            "motivo": "Luna arriba" if a["tipo"] == "sale" else "Luna abajo",
            "desde_dt": centro - dt.timedelta(hours=1),
            "hasta_dt": centro + dt.timedelta(hours=1),
        })
    out = [p for p in out if p["hasta_dt"] >= desde and p["desde_dt"] <= hasta]
    out.sort(key=lambda p: p["desde_dt"])
    return out
