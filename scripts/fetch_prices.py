"""
Para cada acción listada en tickers.json (identificada por ISIN, con símbolo
opcional si cotiza en varias bolsas y quieres fijar una en concreto):
  1. Si no se indica 'symbol', resuelve el símbolo bursátil vía la ISIN API de
     Financial Modeling Prep (con caché en data/isin_map.json). OJO: si el
     ISIN cotiza en varias bolsas, FMP puede devolver cualquiera de ellas —
     para evitar ambigüedad, es más fiable fijar el 'symbol' tú mismo.
  2. Consulta el precio actual de todos los símbolos de una vez.
  3. Actualiza:
       - data/prices.json   -> último precio conocido de cada ISIN
       - data/history.json  -> serie temporal (para el gráfico de evolución)

Requiere la variable de entorno FMP_API_KEY (se pasa como GitHub Secret).
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.environ.get("FMP_API_KEY")
if not API_KEY:
    print("Falta la variable de entorno FMP_API_KEY", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKERS_PATH = os.path.join(ROOT, "tickers.json")
PRICES_PATH = os.path.join(ROOT, "data", "prices.json")
HISTORY_PATH = os.path.join(ROOT, "data", "history.json")
ISIN_MAP_PATH = os.path.join(ROOT, "data", "isin_map.json")

MAX_HISTORY_POINTS = 2000  # evita que el archivo crezca sin límite


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode())


with open(TICKERS_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# Acepta dos formatos en "tickers": strings simples ("ES0148396007") o
# objetos con símbolo fijado ({"isin": "...", "symbol": "...", "label": "..."})
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

isin_map = load_json(ISIN_MAP_PATH, {})  # { ISIN: {symbol, companyName} }

for e in entries:
    isin = e["isin"]
    if e["symbol"]:
        # Símbolo fijado a mano: no hace falta resolver, pero lo guardamos en caché igual
        isin_map[isin] = {"symbol": e["symbol"], "companyName": e["label"] or isin_map.get(isin, {}).get("companyName")}
        continue
    if isin in isin_map:
        continue
    url = f"https://financialmodelingprep.com/stable/search-isin?isin={isin}&apikey={API_KEY}"
    try:
        result = fetch_json(url)
    except urllib.error.URLError as ex:
        print(f"Aviso: no se pudo resolver el ISIN {isin}: {ex}", file=sys.stderr)
        continue
    if not result:
        print(f"Aviso: FMP no devolvió ningún símbolo para el ISIN {isin}", file=sys.stderr)
        continue
    if len(result) > 1:
        print(f"Aviso: {isin} cotiza en {len(result)} mercados distintos, se usó '{result[0]['symbol']}' por defecto. "
              f"Si no es el que quieres, fija 'symbol' explícitamente en tickers.json.", file=sys.stderr)
    chosen = result[0]
    isin_map[isin] = {
        "symbol": chosen.get("symbol"),
        "companyName": chosen.get("companyName") or chosen.get("name"),
    }

os.makedirs(os.path.dirname(ISIN_MAP_PATH), exist_ok=True)
with open(ISIN_MAP_PATH, "w", encoding="utf-8") as f:
    json.dump(isin_map, f, ensure_ascii=False, indent=2)

symbol_to_isins = {}
for e in entries:
    isin = e["isin"]
    entry = isin_map.get(isin)
    if entry and entry.get("symbol"):
        symbol_to_isins.setdefault(entry["symbol"], []).append(isin)

if not symbol_to_isins:
    print("No se pudo resolver ningún símbolo a partir de los ISIN configurados.", file=sys.stderr)
    sys.exit(1)

symbols = ",".join(symbol_to_isins.keys())
quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbols}?apikey={API_KEY}"
try:
    quotes = fetch_json(quote_url)
except urllib.error.URLError as ex:
    print(f"Error consultando precios en FMP: {ex}", file=sys.stderr)
    sys.exit(1)

quotes_by_symbol = {q["symbol"]: q for q in quotes if "symbol" in q}

now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
prices = load_json(PRICES_PATH, {})
history = load_json(HISTORY_PATH, {"points": []})

snapshot = {}
for symbol, isin_list in symbol_to_isins.items():
    q = quotes_by_symbol.get(symbol)
    if not q:
        print(f"Aviso: sin cotización para {symbol}", file=sys.stderr)
        continue
    price = q.get("price")
    for isin in isin_list:
        prices[isin] = {
            "symbol": symbol,
            "companyName": isin_map[isin].get("companyName"),
            "price": price,
            "change": q.get("change"),
            "changesPercentage": q.get("changesPercentage"),
            "updated": now_iso,
        }
        snapshot[isin] = price

history["points"].append({"timestamp": now_iso, "prices": snapshot})
history["points"] = history["points"][-MAX_HISTORY_POINTS:]

os.makedirs(os.path.dirname(PRICES_PATH), exist_ok=True)
with open(PRICES_PATH, "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)
with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print(f"Actualizado: {list(snapshot.keys())}")

