const bankSelect = document.getElementById("bank");
const chequeType = document.getElementById("chequeType");
const dateInput = document.getElementById("date");
const payeeInput = document.getElementById("payee");
const amountInput = document.getElementById("amount");
const wordsMode = document.getElementById("wordsMode");
const amountWordsInput = document.getElementById("amountWords");
const memoInput = document.getElementById("memo");
const padInput = document.getElementById("pad");
const offsetX = document.getElementById("offsetX");
const offsetY = document.getElementById("offsetY");
const stubInput = document.getElementById("stub");
const paperMode = document.getElementById("paperMode");
const cheque = document.getElementById("cheque");
const guideBank = document.getElementById("guideBank");
const dateBoxes = document.getElementById("dateBoxes");

const CHEQUE_WIDTH_MM = 8 * 25.4;
const CHEQUE_HEIGHT_MM = 3.5 * 25.4;

let template = null;
let alignmentMode = false;

function todayIso() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function isManualWords() {
  return wordsMode.value === "manual";
}

function applyWordsMode() {
  const manual = isManualWords();
  amountWordsInput.readOnly = !manual;
  amountWordsInput.placeholder = manual
    ? "Type amount in words…"
    : "Filled automatically from the amount";
  if (!manual) syncAutoWords();
}

function syncAutoWords() {
  if (isManualWords()) return;
  try {
    const data = window.ChequeEngine.formatCheque({
      date: dateInput.value,
      payee: payeeInput.value,
      amount: amountInput.value,
      memo: memoInput.value,
      pad: padInput.checked,
      wordsMode: "auto",
      amountWords: "",
    });
    amountWordsInput.value = data.amount_words || "";
  } catch {
    amountWordsInput.value = "";
  }
}

function calKey(bankId) {
  return `cheque-cal:${bankId}:${chequeType.value || "personal"}`;
}

function loadCal(bankId) {
  try {
    return JSON.parse(localStorage.getItem(calKey(bankId)) || "{}");
  } catch {
    return {};
  }
}

function saveCal() {
  const bankId = bankSelect.value;
  localStorage.setItem(
    calKey(bankId),
    JSON.stringify({
      offset_x_mm: Number(offsetX.value) || 0,
      offset_y_mm: Number(offsetY.value) || 0,
      stub_width_mm: Number(stubInput.value) || 0,
    })
  );
  localStorage.setItem("cheque-words-mode", wordsMode.value || "auto");
  localStorage.setItem("cheque-paper-mode", paperMode.value || "a4");
}

function applyCalToForm(bankId) {
  const cal = loadCal(bankId);
  offsetX.value = cal.offset_x_mm ?? 0;
  offsetY.value = cal.offset_y_mm ?? 0;
  stubInput.value = cal.stub_width_mm ?? template?.stub_width_mm ?? 0;
}

function applyLayout() {
  if (!template) return;
  const fields = template.fields;
  const stub = Number(stubInput.value) || 0;
  const ox = (Number(offsetX.value) || 0) + (template.offset_x_mm || 0) + stub;
  const oy = (Number(offsetY.value) || 0) + (template.offset_y_mm || 0);
  cheque.style.width = `${CHEQUE_WIDTH_MM}mm`;
  cheque.style.height = `${CHEQUE_HEIGHT_MM}mm`;
  const inchesW = (CHEQUE_WIDTH_MM / 25.4).toFixed(2);
  const inchesH = (CHEQUE_HEIGHT_MM / 25.4).toFixed(2);
  const paperLabel =
    paperMode.value === "letter" ? "on Letter paper, top-left" :
    "on A4 paper, top-left";
  document.getElementById("sizeCaption").textContent =
    `Cheque ${inchesW} × ${inchesH} in (${CHEQUE_WIDTH_MM.toFixed(1)} × ${CHEQUE_HEIGHT_MM.toFixed(1)} mm) · ${paperLabel}`;
  cheque.style.transform = `translate(${ox}mm, ${oy}mm)`;
  setPrintPageSize();

  cheque.style.background = template.brand?.paper || "#f4f7f2";
  cheque.style.borderColor = template.brand?.primary || "#1f4d3a";
  guideBank.style.color = template.brand?.primary || "#1f4d3a";
  guideBank.textContent = template.guide?.bank_name || "";

  const date = fields.date;
  dateBoxes.style.left = `${date.x_mm}mm`;
  dateBoxes.style.top = `${date.y_mm}mm`;
  dateBoxes.style.width = `${date.width_mm}mm`;
  dateBoxes.style.height = `${date.height_mm}mm`;
  dateBoxes.innerHTML = "";
  for (let i = 0; i < (date.char_count || 10); i += 1) {
    dateBoxes.appendChild(document.createElement("span"));
  }

  placeEl(document.querySelector(".date-label"), date.x_mm, date.y_mm - 3.6, date.width_mm, 3.4);
  placeEl(document.querySelector(".date-hint"), date.x_mm, date.y_mm + date.height_mm + 0.3, date.width_mm, 3.2);

  const fig = fields.amount_figures;
  const figBox = document.querySelector(".figures-box");
  placeEl(figBox, fig.x_mm, fig.y_mm, fig.width_mm, fig.height_mm);

  const peso = document.querySelector(".peso-sign");
  peso.style.color = template.brand?.primary || "#1f4d3a";
  placeEl(peso, fig.x_mm - 6, fig.y_mm, 6, fig.height_mm);
  peso.style.display = "flex";
  peso.style.alignItems = "center";

  placeEl(document.querySelector(".pay-label"), fields.payee.x_mm, fields.payee.y_mm - 4.6, 50, 4);
  placeEl(document.querySelector(".pesos-label"), fields.amount_words.x_mm, fields.amount_words.y_mm - 4.2, 40, 3.6);

  const sig = fields.signature || { x_mm: 133, y_mm: 61, width_mm: 50, height_mm: 11, count: 1 };
  const sig1 = document.getElementById("sigBox1");
  const sig2 = document.getElementById("sigBox2");
  const sigLabel = document.querySelector(".sig-label");
  if ((sig.count || 1) <= 1) {
    placeEl(sig1, sig.x_mm, sig.y_mm, sig.width_mm, sig.height_mm);
    sig2.style.display = "none";
    placeEl(sigLabel, sig.x_mm, sig.y_mm - 3.6, sig.width_mm, 3.4);
    sigLabel.textContent = "SIGNATURE";
  } else {
    const gap = 2;
    const boxW = (sig.width_mm - gap) / 2;
    placeEl(sig1, sig.x_mm, sig.y_mm, boxW, sig.height_mm);
    placeEl(sig2, sig.x_mm + boxW + gap, sig.y_mm, boxW, sig.height_mm);
    sig2.style.display = "block";
    placeEl(sigLabel, sig.x_mm, sig.y_mm - 3.6, sig.width_mm, 3.4);
    sigLabel.textContent = "SIGNATURES";
  }

  placeField("fDate", date, true);
  placeField("fPayee", fields.payee);
  placeField("fFigures", fig);
  placeField("fWords", fields.amount_words);
  placeField("fMemo", fields.memo);
}

function placeEl(el, x, y, w, h) {
  if (!el) return;
  el.style.left = `${x}mm`;
  el.style.top = `${y}mm`;
  el.style.width = `${w}mm`;
  el.style.height = `${h}mm`;
}

function placeField(id, spec, boxed) {
  const el = document.getElementById(id);
  el.style.left = `${spec.x_mm}mm`;
  el.style.top = `${spec.y_mm}mm`;
  el.style.width = `${spec.width_mm}mm`;
  el.style.height = `${spec.height_mm}mm`;
  el.style.fontSize = `${spec.font_pt || 10}pt`;
  el.dataset.boxed = boxed ? "1" : "";
  el.dataset.chars = String(spec.char_count || 10);
}

function setBoxedDate(text) {
  const el = document.getElementById("fDate");
  const n = Number(el.dataset.chars || 10);
  const padded = (text + " ".repeat(n)).slice(0, n);
  const width = template.fields.date.width_mm;
  el.innerHTML = "";
  [...padded].forEach((ch) => {
    const span = document.createElement("span");
    span.style.width = `${width / n}mm`;
    span.textContent = ch;
    el.appendChild(span);
  });
}

function loadBanks() {
  const data = window.CHEQUE_DATA;
  bankSelect.innerHTML = "";
  data.banks.forEach((bank) => {
    const opt = document.createElement("option");
    opt.value = bank.id;
    opt.textContent = bank.name;
    bankSelect.appendChild(opt);
  });
  bankSelect.value = data.default || "landbank";
}

function loadTemplate() {
  const bankId = bankSelect.value;
  const type = chequeType.value || "personal";
  template = window.CHEQUE_DATA.templates[bankId][type];
  applyCalToForm(bankId);
  applyLayout();
  refreshFields();
}

function refreshFields() {
  try {
    if (!isManualWords()) syncAutoWords();
    const data = window.ChequeEngine.formatCheque({
      date: dateInput.value,
      payee: alignmentMode ? "" : payeeInput.value,
      amount: alignmentMode ? "" : amountInput.value,
      memo: alignmentMode ? "" : memoInput.value,
      pad: padInput.checked,
      alignment: alignmentMode,
      wordsMode: isManualWords() ? "manual" : "auto",
      amountWords: amountWordsInput.value,
    });
    const payee = data.payee || (alignmentMode ? "ALIGNMENT TEST" : "PAYEE NAME");
    const figures = data.amount_figures || "0.00";
    const words = data.amount_words || (alignmentMode ? "***ZERO PESOS AND 00/100***" : "—");
    setBoxedDate(data.date);
    document.getElementById("fPayee").textContent = payee;
    document.getElementById("fFigures").textContent = figures;
    document.getElementById("fWords").textContent = words;
    document.getElementById("fMemo").textContent = data.memo || "";
  } catch (err) {
    document.getElementById("fWords").textContent = err.message || "Invalid amount";
  }
}

function onFormChange() {
  alignmentMode = false;
  saveCal();
  applyLayout();
  refreshFields();
}

function setPrintPageSize() {
  let rule = document.getElementById("printPageRule");
  if (!rule) {
    rule = document.createElement("style");
    rule.id = "printPageRule";
    document.head.appendChild(rule);
  }
  let pageCss = "A4 portrait";
  let sheetW = "210mm";
  let sheetH = "297mm";
  if (paperMode.value === "letter") {
    pageCss = "letter portrait";
    sheetW = "215.9mm";
    sheetH = "279.4mm";
  }
  rule.textContent = `
    @media print {
      @page { size: ${pageCss}; margin: 0; }
      #sheet { width: ${sheetW} !important; height: ${sheetH} !important; }
    }
  `;
}

function printCheque() {
  setPrintPageSize();
  window.print();
}

document.getElementById("printBtn").addEventListener("click", () => {
  alignmentMode = false;
  if (!payeeInput.value.trim() || !amountInput.value.trim()) {
    alert("Enter a payee and an amount before printing.");
    return;
  }
  if (isManualWords() && !amountWordsInput.value.trim()) {
    alert("Enter the amount in words, or switch to Automatic.");
    return;
  }
  refreshFields();
  printCheque();
});

document.getElementById("testBtn").addEventListener("click", () => {
  alignmentMode = true;
  refreshFields();
  printCheque();
  alignmentMode = false;
  refreshFields();
});

wordsMode.addEventListener("change", () => {
  applyWordsMode();
  onFormChange();
});

["change", "input"].forEach((evt) => {
  [bankSelect, chequeType, dateInput, payeeInput, amountInput, amountWordsInput, memoInput, padInput, offsetX, offsetY, stubInput, paperMode].forEach((el) => {
    el.addEventListener(evt, () => {
      if ((el === bankSelect || el === chequeType) && evt === "change") {
        loadTemplate();
        return;
      }
      onFormChange();
    });
  });
});

dateInput.value = todayIso();
wordsMode.value = localStorage.getItem("cheque-words-mode") || "auto";
paperMode.value = localStorage.getItem("cheque-paper-mode") === "letter" ? "letter" : "a4";
applyWordsMode();
setPrintPageSize();
loadBanks();
loadTemplate();
