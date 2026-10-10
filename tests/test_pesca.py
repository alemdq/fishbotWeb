"""Pruebas sin internet: reglas iguales al bot, lector de mareas, pique y armado.

Correr: python -m unittest discover -s tests
"""
import datetime as dt
import itertools
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from pesca import armar, config as C, mareas, pique, reglas  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
TZ = C.TZ


def bot_is_good(rain_mm, rain_prob, wind_speed, wind_compass, wave_height):
    """Copia textual de formatter.is_good_for_fishing del bot de Telegram."""
    if rain_mm is not None and rain_mm > 3:
        return False
    if rain_prob is not None and rain_prob >= 70:
        return False
    if wave_height is not None and wave_height >= 1.6:
        return False
    covered = {"S", "SE", "SO"}
    if wind_compass and wind_compass not in covered and wind_speed is not None:
        if wind_compass in {"N", "NE", "NO"} and wind_speed > 18:
            return False
        if wind_compass in {"E", "O"} and wind_speed > 20:
            return False
    return True


def bot_compass(deg):
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    if deg is None:
        return "?"
    return dirs[round(deg / 45) % 8]


class ReglasIgualesAlBot(unittest.TestCase):
    def test_todas_las_combinaciones(self):
        lluvias = [0, 0.4, 2.9, 3, 3.1, 8]
        probs = [0, 55, 69, 70, 95]
        vientos = [None, 0, 17.9, 18, 18.1, 20, 20.1, 35]
        grados = [None, 0, 22.4, 22.5, 45, 67.5, 90, 112.5, 135, 180, 225, 247.5, 270, 292.5, 315, 337.5, 359]
        olas = [None, 0.8, 1.1, 1.5, 1.59, 1.6, 2.3]
        n = 0
        for ll, pr, vk, g, ol in itertools.product(lluvias, probs, vientos, grados, olas):
            esperado = bot_is_good(ll, pr, vk, bot_compass(g), ol)
            obtenido = not reglas.motivos_no(ll, pr, vk, reglas.rumbo(g), ol)
            self.assertEqual(esperado, obtenido, (ll, pr, vk, g, ol))
            n += 1
        self.assertGreater(n, 20000)

    def test_semaforo(self):
        self.assertEqual(reglas.color_ola(1.1), "verde")
        self.assertEqual(reglas.color_ola(1.2), "amarilla")
        self.assertEqual(reglas.color_ola(1.5), "amarilla")
        self.assertEqual(reglas.color_ola(1.6), "roja")

    def test_mejor_franja(self):
        oks = [1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0]
        self.assertEqual(reglas.mejor_franja([bool(x) for x in oks]), (12, 17))
        self.assertEqual(reglas.mejor_franja([True, True, False, True, True]), (0, 1))
        self.assertIsNone(reglas.mejor_franja([False] * 19))


class LectorDeMareas(unittest.TestCase):
    def test_muestra_real(self):
        dias = mareas.leer_tabla((FIX / "mareas_muestra.html").read_text())
        esperadas = json.loads((FIX / "mareas_esperadas.json").read_text())
        self.assertEqual(sorted(dias), ["2026-10-10", "2026-10-11", "2026-10-31"])
        for fecha, d in dias.items():
            self.assertEqual(d["mareas"], esperadas[fecha]["mareas"], fecha)
            self.assertEqual(d["actividad"], esperadas[fecha]["actividad"], fecha)
        self.assertEqual(dias["2026-10-10"]["sol"], {"sale": "06:09", "pone": "19:04"})


class Pique(unittest.TestCase):
    # Períodos que muestra tablademareas (9 y 10 de octubre de 2026)
    TDM = {
        "2026-10-09T10:50": "mayor", "2026-10-09T23:02": "mayor",
        "2026-10-09T04:57": "menor", "2026-10-09T17:44": "menor",
        "2026-10-10T11:35": "mayor", "2026-10-10T23:48": "mayor",
        "2026-10-10T05:21": "menor", "2026-10-10T18:49": "menor",
    }

    def test_coincide_con_tablademareas(self):
        desde = dt.datetime(2026, 10, 9, tzinfo=TZ)
        ps = pique.periodos(desde, desde + dt.timedelta(days=2))
        for ini, tipo in self.TDM.items():
            t = dt.datetime.fromisoformat(ini).replace(tzinfo=TZ)
            cerca = [p for p in ps if p["tipo"] == tipo and abs((p["desde_dt"] - t).total_seconds()) <= 6 * 60]
            self.assertTrue(cerca, f"falta el período {tipo} de {ini}")


class Bajante(unittest.TestCase):
    def test_cruza_medianoche(self):
        esperadas = json.loads((FIX / "mareas_esperadas.json").read_text())
        ev = mareas.eventos(esperadas, dt.date(2026, 10, 9), dt.date(2026, 10, 10))
        f = lambda d, h: dt.datetime(2026, 10, d, h, tzinfo=TZ)  # noqa: E731
        self.assertTrue(reglas.es_bajante(f(9, 6), ev))     # 05:39 alta → 12:35 baja
        self.assertTrue(reglas.es_bajante(f(9, 12), ev))
        self.assertFalse(reglas.es_bajante(f(9, 13), ev))
        self.assertFalse(reglas.es_bajante(f(9, 18), ev))   # alta recién 18:09
        self.assertTrue(reglas.es_bajante(f(9, 19), ev))
        self.assertTrue(reglas.es_bajante(f(10, 0), ev))    # las 00: el bot no lo marcaba
        self.assertTrue(reglas.es_bajante(f(10, 1), ev))    # baja 01:54


class Armado(unittest.TestCase):
    def test_armado_sin_internet(self):
        ahora = dt.datetime(2026, 10, 10, 13, 0, tzinfo=TZ)
        tiempos, cl, ol = [], {}, {}
        inicio = dt.datetime(2026, 10, 10, tzinfo=TZ)
        for i in range(24 * 8):
            t = inicio + dt.timedelta(hours=i)
            tiempos.append(t.strftime("%Y-%m-%dT%H:%M"))
        n = len(tiempos)
        clima_data = {"hourly": {
            "time": tiempos, "temperature_2m": [15] * n, "weather_code": [2] * n,
            "precipitation_probability": [10] * n, "precipitation": [0] * n, "rain": [0] * n,
            "wind_speed_10m": [25 if 11 <= int(t[11:13]) <= 14 else 10 for t in tiempos],
            "wind_direction_10m": [45] * n, "wind_gusts_10m": [30] * n, "is_day": [1] * n},
            "daily": {"time": ["2026-10-10"], "sunrise": ["2026-10-10T06:09"], "sunset": ["2026-10-10T19:04"]}}
        olas_data = {"hourly": {"time": tiempos, "wave_height": [0.9] * n, "wave_direction": [135] * n, "wave_period": [9] * n}}
        dias_marea = json.loads((RAIZ / "data/cache/mareas-2026-10.json").read_text())["dias"]
        datos = armar.armar(ahora, clima_data, olas_data, dias_marea, {})
        self.assertEqual(len(datos["dias"]), 7)
        hoy = datos["dias"][0]
        self.assertEqual([h["h"] for h in hoy["horas"]][:2], ["06", "07"])
        self.assertEqual(hoy["horas"][-1]["h"], "00")
        self.assertEqual(hoy["mejor"], {"desde": "15", "hasta": "00", "horas": 10})
        self.assertFalse(hoy["horas"][5]["ok"])  # 11 h: NE 25
        self.assertEqual(hoy["horas"][5]["no"][0]["regla"], "viento")
        self.assertEqual(hoy["actividad"], 3)
        self.assertTrue(any(p["tipo"] == "mayor" for p in datos["pique"]))
        json.dumps(datos)  # se puede guardar


if __name__ == "__main__":
    unittest.main()
