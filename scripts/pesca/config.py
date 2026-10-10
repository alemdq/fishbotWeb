"""Configuración: lugar, horarios y reglas.

Las reglas son las mismas que usa el bot de Telegram (formatter.py → is_good_for_fishing).
"""
from zoneinfo import ZoneInfo

# Escollera Norte, Mar del Plata (mismo punto que el bot)
LAT = -38.0
LON = -57.55
TZ_NAME = "America/Argentina/Buenos_Aires"
TZ = ZoneInfo(TZ_NAME)

# Días que muestra la web (hoy + 6)
DIAS = 7

# Horas de cada día: 06 a 23 y las 00 del día siguiente
HORAS = list(range(6, 24)) + [0]

# ─── Reglas del ✅/❌ (idénticas al bot) ───
LLUVIA_MM_MAX = 3          # más de 3 mm de lluvia → no conviene
PROB_LLUVIA_MAX = 70       # 70 % o más de probabilidad → no conviene
OLA_MAX = 1.6              # 1,6 m o más → no conviene
VIENTO_CUBIERTO = {"S", "SE", "SO"}          # la escollera cubre: nunca veta
VIENTO_NORTE = {"N", "NE", "NO"}
VIENTO_NORTE_MAX = 18      # más de 18 km/h → no conviene
VIENTO_LATERAL = {"E", "O"}
VIENTO_LATERAL_MAX = 20    # más de 20 km/h → no conviene

# Semáforo de olas
OLA_VERDE_MAX = 1.1
OLA_AMARILLA_MAX = 1.5

# Pique: una hora cuenta como "de pique" si comparte al menos estos minutos con un período
PIQUE_MIN_SOLAPE = 30

# Fuentes
OPEN_METEO_CLIMA = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_MAR = "https://marine-api.open-meteo.com/v1/marine"
MAREAS_URL = "https://tablademareas.com/ar/buenos-aires/mar-del-plata"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
