"""
Consulta el precio actual de cada acción listada en tickers.json usando el
endpoint público (no oficial) de Yahoo Finance, que no requiere API key y
cubre tanto EEUU como bolsas internacionales. Convierte cualquier precio que
no venga en euros usando el tipo de cambio del momento, para que todos los
cálculos de la app (invertido, resultado, %) se hagan siempre en euros.
Actualiza:
  - data/prices.json   -> último precio conocido de cada ISIN (ya en euros)
  - data/history.json  -> serie temporal (para el gráfico de evolución)

Nota: este endpoint no es una API oficial de Yahoo. Lleva años siendo estable
y es ampliamente usado, pero podría cambiar sin aviso. Si algún símbolo deja
de funcionar, revisa el log de la Action: se avisa símbolo por símbolo y el
resto de acciones no se ve afectado (esa en concreto vuelve a precio manual).
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS_PATH = os.path.join(ROOT, "tickers.json")
PRICES_PATH = os.path.join(ROOT, "data", "prices.json")
HISTORY_PATH = os.path.join(ROOT, "data", "history.json")

MAX_HISTORY_POINTS = 2000  # evita que el archivo crezca sin límite
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; mi-cartera-bot/1.0)"}

_fx_cache = {}  # { "USD": 1.14, "GBP": 0.85, ... } -> unidades de esa divisa por 1 EUR


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def fetch_yahoo_quote(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    result = data.get("chart", {}).get("result")
    if not result:
        raise ValueError("Yahoo no devolvió datos para este símbolo")
    meta = result[0]["meta"]
    price = meta.get("regularMarketPrice")
    prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
    if price is None:
        raise ValueError("Respuesta sin precio")
    change = (price - prev_close) if prev_close else None
    change_pct = (change / prev_close * 100) if change is not None and prev_close else None
    return {
        "price": price,
        "change": change,
        "changesPercentage": change_pct,
        "currency": meta.get("currency"),
    }


def eur_conversion_factor(currency):
    """Devuelve el factor por el que multiplicar un precio en `currency` para
    obtener euros. 1.0 si ya está en euros. Cachea el tipo de cambio para no
    consultarlo más de una vez por ejecución."""
    if not currency or currency.upper() == "EUR":
        return 1.0, 1.0
    # Algunas bolsas de Londres cotizan en peniques (GBp/GBX) en vez de libras.
    pence_divisor = 100.0 if currency in ("GBp", "GBX") else 1.0
    base_currency = "GBP" if currency in ("GBp", "GBX") else currency.upper()
    if base_currency not in _fx_cache:
        pair = f"EUR{base_currency}=X"
        try:
            q = fetch_yahoo_quote(pair)
            _fx_cache[base_currency] = q["price"]  # unidades de base_currency por 1 EUR
        except (urllib.error.URLError, ValueError, KeyError, IndexError) as ex:
            print(f"Aviso: no se pudo obtener el tipo de cambio EUR/{base_currency}: {ex}", file=sys.stderr)
            _fx_cache[base_currency] = None
    rate = _fx_cache[base_currency]
    if not rate:
        return None, pence_divisor
    return 1.0 / rate, pence_divisor


def to_eur(price, currency):
    factor, pence_divisor = eur_conversion_factor(currency)
    if factor is None:
        return None
    return price / pence_divisor * factor


with open(TICKERS_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

raw_entries = config.get("tickers", config.get("isins", []))
entries = []
for item in raw_entries:
    if isinstance(item, str):
        entries.append({"isin": item.strip().upper(), "symbol": None, "label": None})
    else:
        entries.append({
            "isin": item["isin"].strip().upper(),
            "symbol": item.get("symbol"),
            "label": item.get("label"),
        })

benchmarks = config.get("benchmarks", [])

if not entries and not benchmarks:
    print("tickers.json no tiene ninguna acción configurada, nada que hacer.")
    sys.exit(0)

now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
prices = load_json(PRICES_PATH, {})
history = load_json(HISTORY_PATH, {"points": []})

snapshot = {}
any_ok = False
for e in entries:
    isin = e["isin"]
    symbol = e["symbol"] or isin  # si no hay symbol fijado, se intenta con el propio ISIN (rara vez funciona en Yahoo)
    try:
        q = fetch_yahoo_quote(symbol)
    except (urllib.error.URLError, ValueError, KeyError, IndexError) as ex:
        print(f"Aviso: no se pudo obtener precio para {isin} ({symbol}): {ex}", file=sys.stderr)
        continue
    eur_price = to_eur(q["price"], q["currency"])
    if eur_price is None:
        print(f"Aviso: no se pudo convertir a euros el precio de {isin} ({symbol}, {q['currency']}), se omite esta actualización.", file=sys.stderr)
        continue
    prices[isin] = {
        "symbol": symbol,
        "companyName": e["label"],
        "price": eur_price,
        "originalPrice": q["price"],
        "originalCurrency": q["currency"],
        "change": q["change"],
        "changesPercentage": q["changesPercentage"],
        "currency": "EUR",
        "updated": now_iso,
    }
    snapshot[isin] = eur_price
    any_ok = True

benchmark_snapshot = {}
benchmarks_out = load_json(PRICES_PATH.replace("prices.json", "benchmarks.json"), {})
for b in benchmarks:
    symbol = b.get("symbol")
    label = b.get("label") or symbol
    if not symbol:
        continue
    try:
        q = fetch_yahoo_quote(symbol)
    except (urllib.error.URLError, ValueError, KeyError, IndexError) as ex:
        print(f"Aviso: no se pudo obtener precio para el índice {label} ({symbol}): {ex}", file=sys.stderr)
        continue
    # Los índices se usan solo para comparar variación en %, no hace falta
    # convertir su nivel a euros.
    benchmarks_out[label] = {
        "symbol": symbol, "price": q["price"], "changesPercentage": q["changesPercentage"],
        "currency": q["currency"], "updated": now_iso,
    }
    benchmark_snapshot[label] = q["price"]
    any_ok = True

if not any_ok:
    print("No se pudo obtener el precio de ninguna acción ni índice configurado.", file=sys.stderr)
    sys.exit(1)

history["points"].append({"timestamp": now_iso, "prices": snapshot, "benchmarks": benchmark_snapshot})
history["points"] = history["points"][-MAX_HISTORY_POINTS:]

os.makedirs(os.path.dirname(PRICES_PATH), exist_ok=True)
with open(PRICES_PATH, "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)
with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
if benchmarks:
    with open(PRICES_PATH.replace("prices.json", "benchmarks.json"), "w", encoding="utf-8") as f:
        json.dump(benchmarks_out, f, ensure_ascii=False, indent=2)

print(f"Actualizado: {list(snapshot.keys())} · Índices: {list(benchmark_snapshot.keys())}")
