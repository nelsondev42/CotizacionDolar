import unittest
from datetime import datetime, timezone

from scripts.update_quotes import HISTORY_DAYS, amount, parse_html, parse_xml, record_history


class QuoteParserTests(unittest.TestCase):
    def test_parse_guarani_amount(self):
        self.assertEqual(amount("5.680"), 5680)

    def test_parse_cash_sale(self):
        page = b"<p>Dolar en efectivo Compra Gs. 5.600 Venta Gs. 5.680</p>"
        self.assertEqual(parse_html(page, cash=True), 5680)

    def test_reject_unlabelled_rate(self):
        with self.assertRaises(ValueError):
            parse_html(b"<p>Dolar 5.680</p>")

    def test_parse_usd_cash_xml(self):
        data = b"<cotizaciones><moneda><pais>EEUU</pais><tipo>EFECTIVO</tipo><venta>5680</venta></moneda></cotizaciones>"
        self.assertEqual(parse_xml(data), 5680)

    def test_reject_wrong_currency_xml(self):
        data = b"<cotizaciones><moneda><pais>Brasil</pais><tipo>EFECTIVO</tipo><venta>5680</venta></moneda></cotizaciones>"
        with self.assertRaises(ValueError):
            parse_xml(data)


class HistoryTests(unittest.TestCase):
    def test_records_available_sales_for_local_day(self):
        data = {"quotes": [{"id": "atlas", "sale": 6120}, {"id": "itau", "sale": None}]}
        record_history(data, datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc))
        self.assertEqual(data["history"], [{"date": "2026-11-02", "quotes": {"atlas": 6120}}])

    def test_uses_paraguayan_date(self):
        data = {"quotes": [{"id": "atlas", "sale": 6120}]}
        record_history(data, datetime(2026, 11, 2, 2, 0, tzinfo=timezone.utc))
        self.assertEqual(data["history"][0]["date"], "2026-11-01")

    def test_merges_repeated_runs_of_the_same_day(self):
        data = {"quotes": [{"id": "atlas", "sale": 6000}]}
        record_history(data, datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc))
        data["quotes"] = [{"id": "atlas", "sale": 6050}, {"id": "ueno", "sale": 6040}]
        record_history(data, datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc))
        self.assertEqual(len(data["history"]), 1)
        self.assertEqual(data["history"][0]["quotes"], {"atlas": 6050, "ueno": 6040})

    def test_keeps_only_the_last_week(self):
        data = {"quotes": []}
        for offset in range(10):
            data["quotes"] = [{"id": "atlas", "sale": 6000 + offset}]
            record_history(data, datetime(2026, 10, 20 + offset, 13, 0, tzinfo=timezone.utc))
        self.assertEqual(len(data["history"]), HISTORY_DAYS)
        self.assertEqual(data["history"][-1], {"date": "2026-10-29", "quotes": {"atlas": 6009}})


if __name__ == "__main__":
    unittest.main()
