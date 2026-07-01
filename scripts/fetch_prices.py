"""
Consulta el precio actual de cada acción listada en tickers.json usando el
endpoint público (no oficial) de Yahoo Finance, que no requiere API key y
cubre tanto EEUU como bolsas internacionales. Actualiza:
  - data/prices.json   -> último precio conocido de cada ISIN
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

if not entries:
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
    prices[isin] = {
        "symbol": symbol,
        "companyName": e["label"],
        "price": q["price"],
        "change": q["change"],
        "changesPercentage": q["changesPercentage"],
        "currency": q["currency"],
        "updated": now_iso,
    }
    snapshot[isin] = q["price"]
    any_ok = True

if not any_ok:
    print("No se pudo obtener el precio de ninguna acción configurada.", file=sys.stderr)
    sys.exit(1)

history["points"].append({"timestamp": now_iso, "prices": snapshot})
history["points"] = history["points"][-MAX_HISTORY_POINTS:]

os.makedirs(os.path.dirname(PRICES_PATH), exist_ok=True)
with open(PRICES_PATH, "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)
with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print(f"Actualizado: {list(snapshot.keys())}")
