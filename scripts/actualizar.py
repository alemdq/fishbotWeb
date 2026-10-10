"""Corre cada hora en GitHub Actions: junta los datos y escribe web/datos.json.

Uso: python scripts/actualizar.py
Nunca rompe por una fuente caída: usa lo último que se guardó y lo marca en el archivo.
"""
import datetime as dt
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pesca import armar, clima, config as C, mareas  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "data" / "cache"
SALIDA = RAIZ / "web" / "datos.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("actualizar")


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    ahora = dt.datetime.now(C.TZ)
    hoy = ahora.date()

    clima_data, clima_ok = clima.clima(CACHE)
    olas_data, olas_ok = clima.olas(CACHE)
    mareas_dias, mareas_ok, mareas_obt = mareas.rango(
        hoy - dt.timedelta(days=1), hoy + dt.timedelta(days=C.DIAS + 1), hoy, CACHE)

    if not clima_data and not olas_data and not mareas_dias:
        log.error("No hay datos de ninguna fuente ni caché. Se deja el archivo anterior.")
        return 0

    estado = {
        "clima": {"ok": clima_ok, "actualizado": (clima_data or {}).get("_obtenido")},
        "olas": {"ok": olas_ok, "actualizado": (olas_data or {}).get("_obtenido")},
        "mareas": {"ok": mareas_ok, "actualizado": mareas_obt},
    }
    datos = armar.armar(ahora, clima_data, olas_data, mareas_dias, estado)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")))

    log.info("Fuentes: %s", json.dumps(estado, ensure_ascii=False))
    for d in datos["dias"]:
        mj = d["mejor"]
        log.info("%s  mejor: %s  peces: %s  ola máx: %s",
                 d["fecha"], f"{mj['desde']} a {mj['hasta']} h" if mj else "no conviene",
                 d["actividad"], d["ola_max"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
