"""Junta clima, olas, mareas y pique en el archivo que lee la web."""
import datetime as dt

from . import clima as CL
from . import config as C
from . import mareas as MA
from . import pique as PQ
from . import reglas as R


def cielo(codigo):
    """Código WMO de Open-Meteo → tipo de cielo para el ícono."""
    if codigo is None:
        return None
    codigo = int(codigo)
    if codigo in (0, 1):
        return "despejado"
    if codigo == 2:
        return "algo_nublado"
    if codigo == 3:
        return "nublado"
    if codigo in (45, 48):
        return "niebla"
    if 51 <= codigo <= 57:
        return "llovizna"
    if 61 <= codigo <= 67 or 80 <= codigo <= 82:
        return "lluvia"
    if 71 <= codigo <= 77 or codigo in (85, 86):
        return "nieve"
    if codigo >= 95:
        return "tormenta"
    return "nublado"


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M")


def _r1(x):
    return None if x is None else round(float(x), 1)


def _r0(x):
    return None if x is None else int(round(float(x)))


def hora(inicio, w, m, eventos_marea, periodos_pique):
    """Arma una hora: datos, motivos del ❌, bajante y pique."""
    fin = inicio + dt.timedelta(hours=1)
    hay_clima = w is not None and w.get("wind_speed_10m") is not None
    viento_rumbo = R.rumbo(w.get("wind_direction_10m")) if w else None
    ola_m = m.get("wave_height") if m else None

    if hay_clima:
        no = R.motivos_no(w.get("rain"), w.get("precipitation_probability"),
                          w.get("wind_speed_10m"), viento_rumbo, ola_m)
        ok = not no
    else:
        no, ok = [], None  # sin datos: no se puede decir

    return {
        "h": f"{inicio.hour:02d}",
        "ts": _iso(inicio),
        "ok": ok,
        "no": no,
        "cielo": cielo(w.get("weather_code")) if w else None,
        "dia": bool(w.get("is_day")) if w and w.get("is_day") is not None else None,
        "temp": _r1(w.get("temperature_2m")) if w else None,
        "prob": _r0(w.get("precipitation_probability")) if w else None,
        "lluvia": _r1(w.get("rain")) if w else None,
        "precip": _r1(w.get("precipitation")) if w else None,
        "viento": {
            "kmh": _r0(w.get("wind_speed_10m")),
            "raf": _r0(w.get("wind_gusts_10m")),
            "grados": _r0(w.get("wind_direction_10m")),
            "rumbo": viento_rumbo,
        } if hay_clima else None,
        "ola": {
            "m": _r1(ola_m),
            "grados": _r0(m.get("wave_direction")),
            "rumbo": R.rumbo(m.get("wave_direction")),
            "periodo": _r1(m.get("wave_period")),
            "color": R.color_ola(ola_m),
        } if ola_m is not None else None,
        "bajante": R.es_bajante(inicio, eventos_marea),
        "pique": R.es_pique(inicio, fin, periodos_pique),
    }


def armar(ahora, clima_data, olas_data, mareas_dias, estado):
    hoy = ahora.date()
    w_idx = CL.por_hora(clima_data)
    m_idx = CL.por_hora(olas_data)
    sol_om = CL.sol_por_dia(clima_data)

    ev = MA.eventos(mareas_dias, hoy - dt.timedelta(days=1), hoy + dt.timedelta(days=C.DIAS + 1))
    inicio_rango = dt.datetime(hoy.year, hoy.month, hoy.day, tzinfo=C.TZ)
    fin_rango = inicio_rango + dt.timedelta(days=C.DIAS, hours=2)
    periodos = PQ.periodos(inicio_rango, fin_rango)

    dias = []
    for n in range(C.DIAS):
        d = hoy + dt.timedelta(days=n)
        horas = []
        for h in C.HORAS:
            base = d + dt.timedelta(days=1) if h == 0 else d
            inicio = dt.datetime(base.year, base.month, base.day, h, tzinfo=C.TZ)
            clave = _iso(inicio)
            horas.append(hora(inicio, w_idx.get(clave), m_idx.get(clave), ev, periodos))

        oks = [x["ok"] is True for x in horas]
        fr = [{"desde": horas[a]["h"], "hasta": horas[b]["h"], "horas": b - a + 1} for a, b in R.franjas(oks)]
        mj = R.mejor_franja(oks)
        olas_dia = [x["ola"]["m"] for x in horas if x["ola"]]
        vientos = [x["viento"] for x in horas if x["viento"]]
        vmax = max(vientos, key=lambda v: v["kmh"]) if vientos else None
        info = mareas_dias.get(d.isoformat(), {})

        dias.append({
            "fecha": d.isoformat(),
            "sol": sol_om.get(d.isoformat()) or info.get("sol") or {},
            "actividad": info.get("actividad"),
            "mejor": {"desde": horas[mj[0]]["h"], "hasta": horas[mj[1]]["h"], "horas": mj[1] - mj[0] + 1} if mj else None,
            "franjas": fr,
            "ola_max": max(olas_dia) if olas_dia else None,
            "viento_max": {"kmh": vmax["kmh"], "rumbo": vmax["rumbo"]} if vmax else None,
            "horas": horas,
        })

    return {
        "version": 1,
        "generado": ahora.isoformat(timespec="minutes"),
        "lugar": {"nombre": "Escollera Norte", "ciudad": "Mar del Plata", "lat": C.LAT, "lon": C.LON},
        "fuentes": estado,
        "reglas": {
            "lluvia_mm_max": C.LLUVIA_MM_MAX,
            "prob_lluvia_max": C.PROB_LLUVIA_MAX,
            "ola_max": C.OLA_MAX,
            "viento_norte_max": C.VIENTO_NORTE_MAX,
            "viento_lateral_max": C.VIENTO_LATERAL_MAX,
            "ola_verde_max": C.OLA_VERDE_MAX,
            "ola_amarilla_max": C.OLA_AMARILLA_MAX,
        },
        "mareas": [{"ts": _iso(e["dt"]), "tipo": e["tipo"], "altura": e["altura"]} for e in ev],
        "pique": [{"desde": _iso(p["desde_dt"]), "hasta": _iso(p["hasta_dt"]), "tipo": p["tipo"], "motivo": p["motivo"]} for p in periodos],
        "dias": dias,
    }
