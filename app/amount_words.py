"""English amount-in-words for Philippine cheques."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

_ONES = (
    "",
    "ONE",
    "TWO",
    "THREE",
    "FOUR",
    "FIVE",
    "SIX",
    "SEVEN",
    "EIGHT",
    "NINE",
    "TEN",
    "ELEVEN",
    "TWELVE",
    "THIRTEEN",
    "FOURTEEN",
    "FIFTEEN",
    "SIXTEEN",
    "SEVENTEEN",
    "EIGHTEEN",
    "NINETEEN",
)

_TENS = (
    "",
    "",
    "TWENTY",
    "THIRTY",
    "FORTY",
    "FIFTY",
    "SIXTY",
    "SEVENTY",
    "EIGHTY",
    "NINETY",
)

_SCALES = (
    (1_000_000_000, "BILLION"),
    (1_000_000, "MILLION"),
    (1_000, "THOUSAND"),
)


def _under_100(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    if ones == 0:
        return _TENS[tens]
    return f"{_TENS[tens]}-{_ONES[ones]}"


def _under_1000(n: int) -> str:
    if n < 100:
        return _under_100(n)
    hundreds, rest = divmod(n, 100)
    if rest == 0:
        return f"{_ONES[hundreds]} HUNDRED"
    return f"{_ONES[hundreds]} HUNDRED {_under_100(rest)}"


def integer_to_words(n: int) -> str:
    if n < 0:
        raise ValueError("Amount cannot be negative")
    if n == 0:
        return "ZERO"
    parts: list[str] = []
    remaining = n
    for value, name in _SCALES:
        if remaining >= value:
            count, remaining = divmod(remaining, value)
            parts.append(f"{_under_1000(count)} {name}")
    if remaining:
        parts.append(_under_1000(remaining))
    return " ".join(parts)


def amount_in_words(amount: Decimal) -> str:
    """Return e.g. FIFTY THOUSAND PESOS AND 00/100."""
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized < 0:
        raise ValueError("Amount cannot be negative")
    pesos = int(quantized)
    centavos = int((quantized - Decimal(pesos)) * 100)
    peso_word = "PESO" if pesos == 1 else "PESOS"
    return f"{integer_to_words(pesos)} {peso_word} AND {centavos:02d}/100"
