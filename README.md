# Escollera Norte · Pesca

Web con el pronóstico de pesca para la Escollera Norte de Mar del Plata: hoy y los 6 días siguientes, de 06 a 00 h, con las mismas reglas del bot de Telegram.

**Web:** https://alemdq.github.io/fishbotWeb/

## Cómo funciona

- Cada hora, GitHub Actions corre `scripts/actualizar.py`:
  - Pide a Open-Meteo el clima y las olas de 8 días (2 consultas por hora en total, sin importar cuánta gente entre).
  - Lee las mareas y la actividad del día en tablademareas.com **una vez por día** y guarda el mes entero.
  - Calcula los períodos de pique con la posición de la luna (sin internet).
  - Aplica las reglas del ✅/❌ y escribe `web/datos.json`.
- La web solo lee `datos.json`. El celu guarda la última copia, así que sin señal igual se ve el último pronóstico.
- Si una fuente falla, se usa lo último guardado y la web lo avisa. Nada se rompe.
- La caché y el último `datos.json` se guardan en la rama `datos` (se reescribe cada hora, no acumula historial).

## Reglas (iguales al bot)

| Regla | No conviene si… |
|---|---|
| Lluvia | más de 3 mm |
| Probabilidad de lluvia | 70 % o más |
| Olas | 1,6 m o más |
| Viento S / SE / SO | nunca (la escollera cubre) |
| Viento N / NE / NO | más de 18 km/h |
| Viento E / O | más de 20 km/h |

Los números están en `scripts/pesca/config.py`. El pique es informativo: no cambia el ✅/❌.

## Correr a mano

En GitHub: pestaña **Actions** → **Actualizar pronóstico** → **Run workflow**.

## Pruebas

```
pip install -r requirements.txt
python -m unittest discover -s tests
```

Las pruebas comparan las reglas contra el código del bot en más de 20.000 combinaciones, leen una muestra real de tablademareas y verifican el pique contra lo que publica esa página.

Para ver la web con datos de ejemplo: `python tests/demo.py web` y servir la carpeta `web/`.

## Si deja de actualizarse

GitHub pausa los procesos programados de un repo público después de 60 días sin actividad y manda un mail. Para reactivarlo: **Actions** → **Actualizar pronóstico** → **Enable workflow**.
