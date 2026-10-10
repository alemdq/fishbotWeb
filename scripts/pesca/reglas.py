"""Reglas del ✅/❌, semáforo de olas, bajante, pique por hora y mejor franja."""
from . import config as C

RUMBOS = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]


def rumbo(grados):
    """Grados → rumbo de 8 puntos (igual que el bot)."""
    if grados is None:
        return None
    return RUMBOS[round(grados / 45) % 8]


def motivos_no(lluvia_mm, prob, viento_kmh, viento_rumbo, ola_m):
    """Devuelve la lista de reglas que fallan. Lista vacía = conviene.

    Misma lógica que is_good_for_fishing del bot; además devuelve todos los motivos,
    no solo el primero, para poder explicarlos en la web.
    """
    lluvia_mm = lluvia_mm or 0
    prob = prob or 0
    fallas = []
    if lluvia_mm > C.LLUVIA_MM_MAX:
        fallas.append({"regla": "lluvia", "valor": lluvia_mm, "limite": C.LLUVIA_MM_MAX})
    if prob >= C.PROB_LLUVIA_MAX:
        fallas.append({"regla": "prob", "valor": prob, "limite": C.PROB_LLUVIA_MAX})
    if ola_m is not None and ola_m >= C.OLA_MAX:
        fallas.append({"regla": "ola", "valor": ola_m, "limite": C.OLA_MAX})
    if viento_rumbo and viento_rumbo not in C.VIENTO_CUBIERTO and viento_kmh is not None:
        if viento_rumbo in C.VIENTO_NORTE and viento_kmh > C.VIENTO_NORTE_MAX:
            fallas.append({"regla": "viento", "valor": viento_kmh, "limite": C.VIENTO_NORTE_MAX, "rumbo": viento_rumbo})
        if viento_rumbo in C.VIENTO_LATERAL and viento_kmh > C.VIENTO_LATERAL_MAX:
            fallas.append({"regla": "viento", "valor": viento_kmh, "limite": C.VIENTO_LATERAL_MAX, "rumbo": viento_rumbo})
    return fallas


def color_ola(ola_m):
    if ola_m is None:
        return None
    if ola_m <= C.OLA_VERDE_MAX:
        return "verde"
    if ola_m <= C.OLA_AMARILLA_MAX:
        return "amarilla"
    return "roja"


def es_bajante(inicio, eventos):
    """True si el inicio de la hora cae entre una pleamar y la bajamar siguiente.

    `eventos` es la lista ordenada de mareas con fecha y hora completas, así funciona
    también a medianoche y cuando la bajante pasa de un día al otro.
    """
    for a, b in zip(eventos, eventos[1:]):
        if a["tipo"] == "alta" and b["tipo"] == "baja" and a["dt"] <= inicio <= b["dt"]:
            return True
    return False


def es_pique(inicio, fin, periodos, minimo=C.PIQUE_MIN_SOLAPE):
    """True si la hora comparte al menos `minimo` minutos con un período de pique."""
    for p in periodos:
        solape = (min(fin, p["hasta_dt"]) - max(inicio, p["desde_dt"])).total_seconds() / 60
        if solape >= minimo:
            return True
    return False


def franjas(oks):
    """Tramos seguidos de horas que convienen: [(i_desde, i_hasta), ...]."""
    out, ini = [], None
    for i, ok in enumerate(oks):
        if ok and ini is None:
            ini = i
        if not ok and ini is not None:
            out.append((ini, i - 1))
            ini = None
    if ini is not None:
        out.append((ini, len(oks) - 1))
    return out


def mejor_franja(oks):
    """La franja más larga; si empatan, la primera del día."""
    fr = franjas(oks)
    if not fr:
        return None
    return max(fr, key=lambda f: (f[1] - f[0], -f[0]))
