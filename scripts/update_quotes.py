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
    "ueno": ("https://www.ueno.com.py/cambio-de-moneda/", "ueno"),
    "maxicambios": ("https://www.maxicambios.com.py//share", "maxicambios"),
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
        url,
        headers={
            "User-Agent": "CotizacionDolar/1.0",
            "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        return response.read()


def amount(raw):
    value = re.sub(r"[^0-9,\.\-]", "", str(raw).strip())
    if not value or value in {"-", ".", ",", "-.", "-."}:
        raise ValueError("importe no válido")

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        if value.count(",") > 1:
            value = value.replace(",", "")
        else:
            value = value.replace(",", ".")
    elif "." in value and value.count(".") > 1:
        parts = value.split(".")
        if len(parts[-1]) == 3:
            value = "".join(parts)

    parsed = float(value)
    if parsed <= 0 or parsed > 20_000_000:
        raise ValueError("importe fuera de rango")
    return round(parsed)


def clean_text(payload):
    parser = Text()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def parse_html(payload, cash=False):
    text = clean_text(payload)
    if not text:
        raise ValueError("la página no devolvió contenido legible")

    patterns = []
    if cash:
        patterns.append(
            r"(?:usd|d[oó]lar(?:es)?(?:\s+americano(?:s)?)?).{0,250}?(?:en\s+efectivo).{0,250}?(?:venta)\s*(?:gs\.?\s*)?[:\-]?\s*([\d\s.,]+)"
        )
    patterns.extend(
        [
            r"(?:usd|d[oó]lar(?:es)?(?:\s+americano(?:s)?)?).{0,250}?(?:venta)\s*(?:gs\.?\s*)?[:\-]?\s*([\d\s.,]+)",
            r"(?:venta)\s*(?:gs\.?\s*)?[:\-]?\s*([\d\s.,]+)",
        ]
    )

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return amount(match.group(1))
    raise ValueError("no se encontró una venta USD etiquetada")


def parse_maxicambios(payload):
    text = clean_text(payload)
    if not text:
        raise ValueError("la página de Maxicambios no devolvió contenido legible")

    patterns = [
        r"(?:d[oó]lar|usd).{0,220}?(?:venta)\s*(?:gs\.?\s*)?[:\-]?\s*([\d\s.,]+)",
        r"(?:venta)\s*(?:gs\.?\s*)?[:\-]?\s*([\d\s.,]+)",
        r"(?:d[oó]lar|usd).{0,600}?([\d]{3,}(?:[\.,][\d]{3})*(?:[.,][\d]{1,2})?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return amount(match.group(1))

    raise ValueError("no se encontró una venta USD en Maxicambios")


def parse_xml(payload):
    root = ET.fromstring(payload)
    for coin in root.iter():
        if coin.tag.lower() != "moneda":
            continue
        country = (coin.findtext("pais") or "").strip().casefold()
        kind = (coin.findtext("tipo") or "").strip().casefold()
        if country in {"eeuu", "estados unidos", "usa"} and kind in {"efectivo", "dolar"}:
            sale = coin.findtext("venta")
            if sale:
                return amount(sale)
    raise ValueError("el XML no contiene venta USD en efectivo")


def read_quote(url, kind):
    payload = fetch(url)
    if kind == "xml":
        return parse_xml(payload)
    if kind == "maxicambios":
        return parse_maxicambios(payload)
    if kind == "ueno":
        try:
            return parse_html(payload, cash=True)
        except ValueError:
            return parse_html(payload, cash=False)
    return parse_html(payload, cash=False)


def update():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["quotes"] = [quote for quote in data["quotes"] if quote.get("id") != "itau"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    errors = []
    for quote in data["quotes"]:
        if quote["id"] not in SOURCES:
            continue
        url, kind = SOURCES[quote["id"]]
        quote["url"] = url if quote["id"] != "maxicambios" else "https://www.maxicambios.com.py/"
        try:
            quote["sale"] = read_quote(url, kind)
            quote["observedAt"] = now
            quote["status"] = "available"
        except (OSError, TimeoutError, ValueError, ET.ParseError, urllib.error.URLError) as exc:
            errors.append(f'{quote["id"]}: {exc}')
            quote["status"] = "stale" if quote.get("sale") is not None else "unavailable"
    data["updatedAt"] = now
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return errors


if __name__ == "__main__":
    failures = update()
    if failures:
        print("Algunas fuentes no se actualizaron:\n- " + "\n- ".join(failures))
    else:
        print("Cotizaciones actualizadas.")

