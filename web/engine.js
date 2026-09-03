(function (global) {
  const ONES = ["","ONE","TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT","NINE","TEN","ELEVEN","TWELVE","THIRTEEN","FOURTEEN","FIFTEEN","SIXTEEN","SEVENTEEN","EIGHTEEN","NINETEEN"];
  const TENS = ["","","TWENTY","THIRTY","FORTY","FIFTY","SIXTY","SEVENTY","EIGHTY","NINETY"];

  function under100(n) {
    if (n < 20) return ONES[n];
    const tens = Math.floor(n / 10);
    const ones = n % 10;
    return ones === 0 ? TENS[tens] : `${TENS[tens]}-${ONES[ones]}`;
  }

  function under1000(n) {
    if (n < 100) return under100(n);
    const hundreds = Math.floor(n / 100);
    const rest = n % 100;
    if (rest === 0) return `${ONES[hundreds]} HUNDRED`;
    return `${ONES[hundreds]} HUNDRED ${under100(rest)}`;
  }

  function integerToWords(n) {
    if (n === 0) return "ZERO";
    const scales = [[1000000000, "BILLION"], [1000000, "MILLION"], [1000, "THOUSAND"]];
    const parts = [];
    let remaining = n;
    scales.forEach(([value, name]) => {
      if (remaining >= value) {
        const count = Math.floor(remaining / value);
        remaining %= value;
        parts.push(`${under1000(count)} ${name}`);
      }
    });
    if (remaining) parts.push(under1000(remaining));
    return parts.join(" ");
  }

  function amountInWords(amount) {
    const quantized = Math.round(amount * 100) / 100;
    const pesos = Math.trunc(quantized);
    const centavos = Math.round((quantized - pesos) * 100);
    const pesoWord = pesos === 1 ? "PESO" : "PESOS";
    return `${integerToWords(pesos)} ${pesoWord} AND ${String(centavos).padStart(2, "0")}/100`;
  }

  function padSymbols(text, enabled) {
    const cleaned = text.trim().replace(/\s+/g, " ");
    if (!cleaned) return "";
    return enabled ? `***${cleaned}***` : cleaned;
  }

  function formatDateBoxed(iso) {
    if (!iso) {
      const d = new Date();
      iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    }
    const [y, m, day] = iso.split("-");
    return `${m}-${day}-${y}`;
  }

  function parseAmount(raw) {
    const text = String(raw).trim().replace(/₱/g, "").replace(/,/g, "").replace(/ /g, "");
    if (!text) return null;
    const amount = Number(text);
    if (!Number.isFinite(amount) || amount < 0) throw new Error("Amount must be a valid number");
    return Math.round(amount * 100) / 100;
  }

  function formatAmountFigures(amount) {
    return amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatCheque({ date, payee, amount, memo, pad, alignment, wordsMode, amountWords }) {
    if (alignment) {
      return {
        date: "00-00-0000",
        payee: "ALIGNMENT TEST",
        amount_figures: "0,000.00",
        amount_words: "***ZERO PESOS AND 00/100***",
        memo: "TEST",
      };
    }
    const parsed = amount ? parseAmount(amount) : null;
    let words = "";
    if (wordsMode === "manual") {
      words = padSymbols(String(amountWords || "").toUpperCase(), pad);
    } else if (parsed != null) {
      words = padSymbols(amountInWords(parsed), pad);
    }
    return {
      date: formatDateBoxed(date),
      payee: padSymbols((payee || "").toUpperCase(), pad),
      amount_figures: parsed == null ? "" : formatAmountFigures(parsed),
      amount_words: words,
      memo: (memo || "").trim(),
    };
  }

  global.ChequeEngine = { formatCheque, parseAmount, amountInWords };
})(window);
