import unittest

from scripts.update_quotes import amount, parse_html, parse_xml


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


if __name__ == "__main__":
    unittest.main()
