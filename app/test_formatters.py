from datetime import date
from decimal import Decimal

from app.amount_words import amount_in_words
from app.pchc import format_amount_figures, format_amount_words, format_date_boxed, format_payee, parse_amount
from app.templates_loader import load_bank


def test_amount_words() -> None:
    assert amount_in_words(Decimal("0")) == "ZERO PESOS AND 00/100"
    assert amount_in_words(Decimal("1")) == "ONE PESO AND 00/100"
    assert amount_in_words(Decimal("21.05")) == "TWENTY-ONE PESOS AND 05/100"
    assert "FIFTY THOUSAND" in amount_in_words(Decimal("50000"))
    assert "ONE MILLION" in amount_in_words(Decimal("1000000.25"))


def test_pchc() -> None:
    assert format_date_boxed(date(2026, 8, 16)) == "08-16-2026"
    assert len(format_date_boxed(date(2026, 8, 16))) == 10
    assert parse_amount("10,000.50") == Decimal("10000.50")
    assert format_amount_figures(Decimal("10000")) == "10,000.00"
    assert format_payee("juan dela cruz", True) == "***JUAN DELA CRUZ***"
    words = format_amount_words(Decimal("10000"), True)
    assert words.startswith("***") and words.endswith("***")
    assert "PESOS" in words


def test_landbank_template() -> None:
    template = load_bank("landbank", "personal")
    assert template["id"] == "landbank"
    assert template["fields"]["date"]["char_count"] == 10
    assert template["fields"]["signature"]["count"] == 1
    corp = load_bank("landbank", "corporate")
    assert corp["fields"]["signature"]["count"] == 2
    bdo = load_bank("bdo", "personal")
    assert bdo["fields"]["date"]["x_mm"] != template["fields"]["date"]["x_mm"]


if __name__ == "__main__":
    test_amount_words()
    test_pchc()
    test_landbank_template()
    print("ok")
