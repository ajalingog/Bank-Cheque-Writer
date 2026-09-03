"""PCHC new-check-design formatters (date, figures, payee, words)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.amount_words import amount_in_words

MAX_AMOUNT = Decimal("999999999999.99")


def format_date_boxed(issue_date: date) -> str:
    """MM-DD-YYYY with dashes only — exactly 10 characters for the date boxes."""
    return issue_date.strftime("%m-%d-%Y")


def parse_amount(raw: str) -> Decimal:
    text = raw.strip().replace("₱", "").replace(",", "").replace(" ", "")
    if not text:
        raise ValueError("Enter an amount")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Amount must be a valid number") from exc
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    if amount > MAX_AMOUNT:
        raise ValueError("Amount is too large")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_amount_figures(amount: Decimal) -> str:
    """Standard figures with commas and a period. No peso sign, no padding symbols."""
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized:,.2f}"


def pad_symbols(text: str, enabled: bool, symbol: str = "*") -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    if not enabled:
        return cleaned
    wrap = symbol * 3
    return f"{wrap}{cleaned}{wrap}"


def format_payee(name: str, pad: bool) -> str:
    return pad_symbols(name.upper(), pad)


def format_amount_words(amount: Decimal, pad: bool) -> str:
    return pad_symbols(amount_in_words(amount), pad)


def format_manual_amount_words(text: str, pad: bool) -> str:
    """Use user-typed amount-in-words; uppercase and optional *** padding."""
    return pad_symbols(text.upper(), pad)


def alignment_sample() -> dict:
    return {
        "date": "00-00-0000",
        "payee": "ALIGNMENT TEST",
        "amount_figures": "0,000.00",
        "amount_words": "***ZERO PESOS AND 00/100***",
        "memo": "TEST",
    }
