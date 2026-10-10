"""Mareas y actividad del día desde tablademareas.com.

La página trae la tabla del mes completo: mareas, alturas, salida/puesta del sol
y la actividad de pesca (0 a 3 peces). Se lee una vez por día y se guarda.
"""
import datetime as dt
import json
import logging
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from . import config as C

log = logging.getLogger(__name__)


def _hora_24(texto):
    """'1:54 am' → '01:54'; '6:54 pm' → '18:54'."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", texto.strip().lower())
    if not m:
        return None
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3)
    if ap == "pm" and h != 12:
        h += 12
    elif ap == "am" and h == 12:
        h = 0
    return f"{h:02d}:{mi}"


def leer_tabla(html):
    """HTML de la página → {'2026-10-10': {'mareas': [...], 'actividad': 3, 'sol': {...}}}."""
    soup = BeautifulSoup(html, "html.parser")
    dias = {}
    for fila in soup.find_all("tr", class_="tabla_mareas_fila"):
        m = re.search(r"Day\('(\d{4})-(\d{1,2})-(\d{1,2})'\)", fila.get("onclick", ""))
        if not m:
            continue
        fecha = f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        if fecha in dias:
            continue  # la tabla aparece repetida en la página

        mareas = []
        for celda in fila.find_all("td", class_="tabla_mareas_marea"):
            hora_div = celda.find("div", class_="tabla_mareas_marea_hora")
            hora = _hora_24(hora_div.get_text(" ", strip=True)) if hora_div else None
            if not hora:
                continue
            if celda.find("div", class_="tabla_mareas_marea_pleamar"):
                tipo = "alta"
            elif celda.find("div", class_="tabla_mareas_marea_bajamar"):
                tipo = "baja"
            else:
                continue
            altura = None
            alt = celda.find("span", class_="tabla_mareas_marea_altura_numero")
            if alt:
                try:
                    altura = float(alt.get_text(strip=True).replace(",", "."))
                except ValueError:
                    pass
            mareas.append({"hora": hora, "tipo": tipo, "altura": altura})

        sol = {}
        sale = fila.find("div", class_="tabla_mareas_salida_puesta_sol_salida")
        pone = fila.find("div", class_="tabla_mareas_salida_puesta_sol_puesta")
        if sale:
            sol["sale"] = _hora_24(sale.get_text(" ", strip=True))
        if pone:
            sol["pone"] = _hora_24(pone.get_text(" ", strip=True))

        act = fila.find("td", class_="tabla_mareas_actividad")
        actividad = len(act.find_all("span", class_="icon-ic_pez_leyenda")) if act else None

        dias[fecha] = {"mareas": mareas, "actividad": actividad, "sol": sol}
    return dias


def _bajar_mes(anio, mes, hoy):
    """Pide la página del mes. El mes actual con GET; otro mes con el formulario de la página."""
    headers = {"User-Agent": C.USER_AGENT}
    if (anio, mes) == (hoy.year, hoy.month):
        r = requests.get(C.MAREAS_URL, headers=headers, timeout=20)
    else:
        r = requests.post(C.MAREAS_URL, headers=headers, data={"fecha": f"{anio:04d}-{mes:02d}-01"}, timeout=20)
    r.raise_for_status()
    return r.text


def mes(anio, mes_, hoy, carpeta: Path):
    """Datos del mes, con caché diaria. Si la página falla, usa lo último guardado."""
    archivo = carpeta / f"mareas-{anio:04d}-{mes_:02d}.json"
    guardado = None
    if archivo.exists():
        try:
            guardado = json.loads(archivo.read_text())
        except (OSError, ValueError):
            guardado = None

    if guardado and guardado.get("obtenido") == hoy.isoformat():
        return guardado, True

    try:
        dias = leer_tabla(_bajar_mes(anio, mes_, hoy))
        dias = {k: v for k, v in dias.items() if k.startswith(f"{anio:04d}-{mes_:02d}-")}
        if len(dias) < 28:
            raise ValueError(f"la tabla trajo solo {len(dias)} días")
        nuevo = {"obtenido": hoy.isoformat(), "dias": dias}
        archivo.write_text(json.dumps(nuevo, ensure_ascii=False, indent=1))
        log.info("Mareas %04d-%02d actualizadas (%d días)", anio, mes_, len(dias))
        return nuevo, True
    except Exception as e:  # noqa: BLE001 — cualquier falla: seguimos con la caché
        log.warning("No se pudieron leer las mareas %04d-%02d: %s", anio, mes_, e)
        return guardado, False


def rango(desde: dt.date, hasta: dt.date, hoy: dt.date, carpeta: Path):
    """Mareas de todos los días entre `desde` y `hasta` (pueden ser dos meses)."""
    meses = sorted({(d.year, d.month) for d in (desde, hasta)})
    dias, ok, obtenido = {}, True, None
    for anio, m in meses:
        datos, fresco = mes(anio, m, hoy, carpeta)
        ok = ok and fresco
        if datos:
            dias.update(datos["dias"])
            obtenido = min(obtenido or datos["obtenido"], datos["obtenido"])
        else:
            ok = False
    return dias, ok, obtenido


def eventos(dias, desde: dt.date, hasta: dt.date):
    """Lista ordenada de mareas con fecha y hora completas."""
    out = []
    d = desde
    while d <= hasta:
        for m in dias.get(d.isoformat(), {}).get("mareas", []):
            h, mi = map(int, m["hora"].split(":"))
            out.append({
                "dt": dt.datetime(d.year, d.month, d.day, h, mi, tzinfo=C.TZ),
                "tipo": m["tipo"],
                "altura": m["altura"],
            })
        d += dt.timedelta(days=1)
    out.sort(key=lambda e: e["dt"])
    return out
