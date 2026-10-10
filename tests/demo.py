"""Arma un datos.json de ejemplo (clima inventado, mareas y pique reales) para ver la web sin internet.

Uso: python tests/demo.py CARPETA_DESTINO
"""
import datetime as dt
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
from pesca import armar, config as C  # noqa: E402

ahora = dt.datetime.now(C.TZ).replace(second=0, microsecond=0)
inicio = dt.datetime(ahora.year, ahora.month, ahora.day, tzinfo=C.TZ)
t, temp, code, prob, prec, rain, ws, wd, wg, isday, wh, wdir, wp = ([] for _ in range(13))
for i in range(24 * 8):
    x = inicio + dt.timedelta(hours=i)
    h, d = x.hour, i // 24
    t.append(x.strftime("%Y-%m-%dT%H:%M"))
    temp.append(10 + 4 * math.sin((h - 9) / 24 * 2 * math.pi))
    lluvia = d == 1 and 9 <= h <= 13
    code.append(61 if lluvia else (2 if h % 5 else 3))
    prob.append(85 if lluvia else (20 + (h * 7 + d * 13) % 50))
    rain.append(4.2 if (lluvia and h == 11) else (0.6 if lluvia else 0))
    prec.append(rain[-1])
    ws.append(10 + ((h * 3 + d * 5) % 16))
    wd.append([0, 45, 90, 180, 225, 315][(h // 4 + d) % 6])
    wg.append(ws[-1] + 12)
    isday.append(1 if 6 <= h <= 19 else 0)
    wh.append(round(0.7 + 0.5 * math.sin((i + 3) / 11) + (0.6 if d == 2 else 0), 2))
    wdir.append(135)
    wp.append(9)
clima = {"hourly": {"time": t, "temperature_2m": temp, "weather_code": code, "precipitation_probability": prob,
                    "precipitation": prec, "rain": rain, "wind_speed_10m": ws, "wind_direction_10m": wd,
                    "wind_gusts_10m": wg, "is_day": isday},
         "daily": {"time": [], "sunrise": [], "sunset": []}}
olas = {"hourly": {"time": t, "wave_height": wh, "wave_direction": wdir, "wave_period": wp}}
mareas = {}
for f in sorted((RAIZ / "data/cache").glob("mareas-*.json")):
    mareas.update(json.loads(f.read_text())["dias"])
estado = {"clima": {"ok": True, "actualizado": ahora.isoformat(timespec="minutes")},
          "olas": {"ok": True, "actualizado": ahora.isoformat(timespec="minutes")},
          "mareas": {"ok": True, "actualizado": ahora.date().isoformat()}}
datos = armar.armar(ahora - dt.timedelta(minutes=12), clima, olas, mareas, estado)
destino = Path(sys.argv[1]) / "datos.json"
destino.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
print("ok", destino, len(destino.read_text()) // 1024, "KB")
