#!/usr/bin/env python3
"""Refresh verifiable USD/PYG sale quotes; retain previous values on source errors."""

import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cotizaciones.json"
SOURCES = {
    "atlas": ("https://www.bancoatlas.com.py/web", "html"),
    "itau": ("https://www.itau.com.py/", "html"),
    "ueno": ("https://www.ueno.com.py/cambio-de-moneda/", "ueno"),
    "maxicambios": ("https://cotizext.maxicambios.com.py/maxicambios4.xml", "xml"),
}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, content):
        if content.strip():
            self.parts.append(content.strip())


def fetch(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "CotizacionDolar/1.0", "Accept": "text/html,application/xml"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        return response.read()


def amount(raw):
    value = raw.strip().replace("Gs.", "").replace("Gs", "").strip()
    value = value.replace(".", "").replace(",", ".")
    parsed = float(value)
    if parsed <= 0 or parsed > 20_000_000:
        raise ValueError("importe fuera de rango")
    return round(parsed)


def parse_html(payload, cash=False):
    parser = Text()
    parser.feed(payload.decode("utf-8", errors="replace"))
    text = re.sub(r"\s+", " ", " ".join(parser.parts))
    currency = r"(?:USD|D[oó]lar(?:es)?(?:\s+americano(?:s)?)?)"
    modality = r".{0,180}?en\s+efectivo" if cash else ""
    pattern = currency + modality + r".{0,240}?Venta(?:\s+Gs\.?)?\s*[:\-]?\s*([\d.,]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("no se encontró una venta USD etiquetada")
    return amount(match.group(1))


def parse_xml(payload):
    root = ET.fromstring(payload)
    for coin in root.findall(".//moneda"):
        country = (coin.findtext("pais") or "").strip().casefold()
        kind = (coin.findtext("tipo") or "").strip().casefold()
        if country in {"eeuu", "estados unidos", "usa"} and kind == "efectivo":
            sale = coin.findtext("venta")
            if sale:
                return amount(sale)
    raise ValueError("el XML no contiene venta USD en efectivo")


def read_quote(url, kind):
    payload = fetch(url)
    if kind == "xml":
        return parse_xml(payload)
    return parse_html(payload, cash=kind == "ueno")


def update():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    errors = []
    for quote in data["quotes"]:
        url, kind = SOURCES[quote["id"]]
        quote["url"] = url if quote["id"] != "maxicambios" else "https://www.maxicambios.com.py/"
        try:
            quote["sale"] = read_quote(url, kind)
            quote["observedAt"] = now
            quote["status"] = "available"
        except (OSError, TimeoutError, ValueError, ET.ParseError, urllib.error.URLError) as exc:
            errors.append(f'{quote["id"]}: {exc}')
            quote["status"] = "stale" if quote["sale"] is not None else "unavailable"
    data["updatedAt"] = now
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return errors


if __name__ == "__main__":
    failures = update()
    if failures:
        print("Algunas fuentes no se actualizaron:\n- " + "\n- ".join(failures))
    else:
        print("Cotizaciones actualizadas.")
