"""Main cheque writer window."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, QMarginsF, QSizeF, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QPageLayout, QPageSize, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog, QPrinterInfo
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.cheque_painter import Calibration, DrawOptions, page_size_mm, paint_cheque
from app.alignment_dialog import AlignmentDialog
from app.pchc import (
    alignment_sample,
    format_amount_figures,
    format_amount_words,
    format_date_boxed,
    format_manual_amount_words,
    format_payee,
    parse_amount,
)
from app.paths import web_dir
from app.preview import ChequePreview
from app.settings_store import get_calibration, load_settings, save_settings, set_calibration
from app.templates_loader import bank_choices, load_bank

APP_STYLE = """
QWidget#MainRoot {
    background: #cfd9cc;
    font-size: 13px;
    color: #122018;
}
QFrame#SidePanel {
    background: #f7faf6;
    border-right: 1px solid #c3d0c2;
}
QLabel#AppTitle {
    font-size: 18px;
    font-weight: 700;
    color: #1f4d3a;
}
QLabel#AppLede, QLabel#Hint, QLabel#FieldHint, QLabel#StatusBar {
    color: #5b6b62;
    font-size: 12px;
}
QLabel#PreviewTitle {
    font-size: 13px;
    font-weight: 600;
    color: #1f4d3a;
}
QGroupBox {
    font-weight: 600;
    color: #1f4d3a;
    border: 1px solid #c3d0c2;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLineEdit, QComboBox, QDateEdit {
    padding: 7px 9px;
    min-height: 28px;
    border: 1px solid #b7c6b6;
    border-radius: 6px;
    background: #ffffff;
    selection-background-color: #2e6b52;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #2e6b52;
}
QLineEdit[readOnly="true"] {
    background: #eef3ef;
    color: #355343;
}
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #122018;
}
QPushButton {
    padding: 9px 14px;
    border-radius: 6px;
    border: 0;
    font-weight: 600;
    background: #4d6558;
    color: #ffffff;
}
QPushButton:hover { background: #3f5448; }
QPushButton:pressed { background: #33463c; }
QPushButton#PrimaryBtn {
    background: #1f4d3a;
    padding: 11px 16px;
    font-size: 14px;
}
QPushButton#PrimaryBtn:hover { background: #2e6b52; }
QPushButton#GhostBtn {
    background: transparent;
    color: #1f4d3a;
    border: 1px solid #b7c6b6;
}
QPushButton#GhostBtn:hover {
    background: #eef3ef;
}
QScrollArea { border: 0; background: transparent; }
"""


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MainRoot")
        self.setWindowTitle("Philippine Cheque Writer")
        self.resize(1220, 760)
        self.setMinimumSize(960, 640)
        self.settings = load_settings()
        self._build()
        self._restore()
        self._refresh_preview()
        self._update_status()

    def _build(self) -> None:
        self.bank = QComboBox()
        for bank_id, name in bank_choices():
            self.bank.addItem(name, bank_id)
        self.cheque_type = QComboBox()
        self.cheque_type.addItem("Personal", "personal")
        self.cheque_type.addItem("Corporate", "corporate")

        self.issue_date = QDateEdit()
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat("MM-dd-yyyy")
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setDateRange(QDate(2000, 1, 1), QDate(2100, 12, 31))

        self.payee = QLineEdit()
        self.payee.setPlaceholderText("One payee name, or CASH")
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("e.g. 10000.00")
        self.amount_words = QLineEdit()
        self.memo = QLineEdit()
        self.memo.setPlaceholderText("Optional note on the cheque")

        self.words_auto = QRadioButton("Automatic — generate from the amount")
        self.words_manual = QRadioButton("Manual — type the words yourself")
        self.words_auto.setChecked(True)
        self.words_group = QButtonGroup(self)
        self.words_group.addButton(self.words_auto)
        self.words_group.addButton(self.words_manual)

        self.pad = QCheckBox("Wrap payee and amount in words with ***")
        self.pad.setChecked(True)

        # Header
        title = QLabel("Philippine Cheque Writer")
        title.setObjectName("AppTitle")
        lede = QLabel(
            "Fill the form → check the live preview → Print onto real cheque stock at 100%."
        )
        lede.setObjectName("AppLede")
        lede.setWordWrap(True)

        # Bank section
        bank_form = QFormLayout()
        bank_form.setSpacing(10)
        bank_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bank_form.addRow("Bank", self.bank)
        bank_form.addRow("Cheque type", self.cheque_type)
        bank_box = QGroupBox("1. Select bank")
        bank_box.setLayout(bank_form)

        # Details section
        details_form = QFormLayout()
        details_form.setSpacing(10)
        details_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        details_form.addRow("Date", self.issue_date)
        details_form.addRow("Payee", self.payee)
        details_form.addRow("Amount (PHP)", self.amount)
        details_form.addRow("Memo", self.memo)
        details_box = QGroupBox("2. Cheque details")
        details_box.setLayout(details_form)

        # Words section
        words_layout = QVBoxLayout()
        words_layout.setSpacing(8)
        words_layout.addWidget(self.words_auto)
        words_layout.addWidget(self.words_manual)
        words_hint = QLabel("Words printed on the PESOS line of the cheque.")
        words_hint.setObjectName("FieldHint")
        words_hint.setWordWrap(True)
        words_layout.addWidget(words_hint)
        words_layout.addWidget(self.amount_words)
        words_layout.addWidget(self.pad)
        words_box = QGroupBox("3. Amount in words")
        words_box.setLayout(words_layout)

        # Actions
        self.print_btn = QPushButton("Print cheque")
        self.print_btn.setObjectName("PrimaryBtn")
        self.print_btn.setDefault(True)
        self.print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn = QPushButton("Print preview")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        align_btn = QPushButton("Fix alignment…")
        align_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        web_btn = QPushButton("Open website")
        web_btn.setObjectName("GhostBtn")
        web_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.print_btn.clicked.connect(self._print)
        preview_btn.clicked.connect(self._print_preview)
        align_btn.clicked.connect(self._align)
        web_btn.clicked.connect(self._open_website)

        actions = QVBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.print_btn)
        secondary = QHBoxLayout()
        secondary.setSpacing(8)
        secondary.addWidget(preview_btn)
        secondary.addWidget(align_btn)
        actions.addLayout(secondary)
        actions.addWidget(web_btn)

        hint = QLabel(
            "Tip: Load a cheque (or photocopy), use Fix alignment once per bank/printer, "
            "then print at Actual size / 100%. Sign by hand after printing."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)

        self.status = QLabel("")
        self.status.setObjectName("StatusBar")
        self.status.setWordWrap(True)

        side_inner = QVBoxLayout()
        side_inner.setContentsMargins(20, 20, 20, 16)
        side_inner.setSpacing(12)
        side_inner.addWidget(title)
        side_inner.addWidget(lede)
        side_inner.addWidget(bank_box)
        side_inner.addWidget(details_box)
        side_inner.addWidget(words_box)
        side_inner.addLayout(actions)
        side_inner.addWidget(hint)
        side_inner.addStretch(1)
        side_inner.addWidget(self.status)

        side_widget = QWidget()
        side_widget.setLayout(side_inner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(side_widget)

        side = QFrame()
        side.setObjectName("SidePanel")
        side.setFixedWidth(400)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.addWidget(scroll)

        preview_title = QLabel("Live preview — what will print")
        preview_title.setObjectName("PreviewTitle")
        self.preview = ChequePreview()
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        preview_wrap = QVBoxLayout()
        preview_wrap.setContentsMargins(20, 18, 20, 18)
        preview_wrap.setSpacing(10)
        preview_wrap.addWidget(preview_title)
        preview_wrap.addWidget(self.preview, 1)
        preview_panel = QWidget()
        preview_panel.setLayout(preview_wrap)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(side)
        root.addWidget(preview_panel, 1)

        self.bank.currentIndexChanged.connect(self._on_bank_changed)
        self.cheque_type.currentIndexChanged.connect(self._on_bank_changed)
        self.issue_date.dateChanged.connect(self._on_form_changed)
        self.payee.textChanged.connect(self._on_form_changed)
        self.amount.textChanged.connect(self._on_form_changed)
        self.words_group.buttonClicked.connect(self._on_words_mode_changed)
        self.amount_words.textChanged.connect(self._on_form_changed)
        self.memo.textChanged.connect(self._on_form_changed)
        self.pad.toggled.connect(self._on_form_changed)
        self._apply_words_mode()
        self.setStyleSheet(APP_STYLE)

    def _on_form_changed(self) -> None:
        self._refresh_preview()
        self._update_status()

    def _update_status(self) -> None:
        missing: list[str] = []
        if not self.payee.text().strip():
            missing.append("payee")
        if not self.amount.text().strip():
            missing.append("amount")
        elif self._amount_error():
            missing.append("valid amount")
        if self._is_manual_words() and not self.amount_words.text().strip():
            missing.append("amount in words")
        if missing:
            self.status.setText("Almost ready — still need: " + ", ".join(missing) + ".")
            self.print_btn.setEnabled(False)
        else:
            bank = self.bank.currentText()
            self.status.setText(f"Ready to print · {bank} · {self.cheque_type.currentText()}")
            self.print_btn.setEnabled(True)

    def _amount_error(self) -> str | None:
        try:
            parse_amount(self.amount.text())
            return None
        except ValueError as exc:
            return str(exc)

    def _restore(self) -> None:
        bank_id = self.settings.get("bank_id", "landbank")
        idx = self.bank.findData(bank_id)
        self.bank.setCurrentIndex(idx if idx >= 0 else 0)
        type_idx = self.cheque_type.findData(self.settings.get("cheque_type", "personal"))
        self.cheque_type.setCurrentIndex(type_idx if type_idx >= 0 else 0)
        if self.settings.get("words_mode", "auto") == "manual":
            self.words_manual.setChecked(True)
        else:
            self.words_auto.setChecked(True)
        self.pad.setChecked(bool(self.settings.get("pad_symbols", True)))
        self._apply_words_mode()

    def _words_mode(self) -> str:
        return "manual" if self.words_manual.isChecked() else "auto"

    def _is_manual_words(self) -> bool:
        return self._words_mode() == "manual"

    def _apply_words_mode(self) -> None:
        manual = self._is_manual_words()
        self.amount_words.setReadOnly(not manual)
        self.amount_words.setPlaceholderText(
            "Type amount in words…" if manual else "Filled automatically from the amount"
        )
        if not manual:
            self._sync_auto_words()

    def _on_words_mode_changed(self, *_args) -> None:
        self._apply_words_mode()
        self.settings["words_mode"] = self._words_mode()
        save_settings(self.settings)
        self._on_form_changed()

    def _sync_auto_words(self) -> None:
        if self._is_manual_words():
            return
        pad = self.pad.isChecked()
        try:
            amount = parse_amount(self.amount.text()) if self.amount.text().strip() else None
        except ValueError:
            amount = None
        text = format_amount_words(amount, pad) if amount is not None else ""
        if self.amount_words.text() != text:
            self.amount_words.blockSignals(True)
            self.amount_words.setText(text)
            self.amount_words.blockSignals(False)

    def _resolve_amount_words(self, amount: Decimal | None, pad: bool) -> str:
        if self._is_manual_words():
            return format_manual_amount_words(self.amount_words.text(), pad)
        if amount is None:
            return ""
        return format_amount_words(amount, pad)

    def _bank_id(self) -> str:
        return str(self.bank.currentData())

    def _cheque_type(self) -> str:
        return str(self.cheque_type.currentData() or "personal")

    def _printer_name(self) -> str:
        return self.settings.get("printer_name") or QPrinterInfo.defaultPrinterName()

    def _template(self) -> dict:
        return load_bank(self._bank_id(), self._cheque_type())

    def _calibration(self) -> Calibration:
        stored = get_calibration(self.settings, self._printer_name(), self._bank_id(), self._cheque_type())
        template = self._template()
        stub = stored["stub_width_mm"]
        if stub == 0:
            stub = float(template.get("stub_width_mm", 0))
        return Calibration(
            offset_x_mm=stored["offset_x_mm"],
            offset_y_mm=stored["offset_y_mm"],
            stub_width_mm=stub,
        )

    def _paper_mode(self) -> str:
        return str(self.settings.get("paper_mode", "cheque"))

    def _feed(self) -> str:
        return str(self.settings.get("feed", "top_first"))

    def _issue_date(self) -> date:
        qd = self.issue_date.date()
        return date(qd.year(), qd.month(), qd.day())

    def _field_values(self, *, alignment: bool = False) -> dict[str, str] | None:
        if alignment:
            return alignment_sample()
        pad = self.pad.isChecked()
        try:
            amount = parse_amount(self.amount.text()) if self.amount.text().strip() else Decimal("0.00")
        except ValueError as exc:
            QMessageBox.warning(self, "Amount", str(exc))
            return None
        if self._is_manual_words() and not self.amount_words.text().strip():
            QMessageBox.warning(self, "Amount in words", "Enter the amount in words, or switch to Automatic.")
            return None
        payee = format_payee(self.payee.text(), pad)
        words = self._resolve_amount_words(amount if self.amount.text().strip() else None, pad)
        figures = format_amount_figures(amount) if self.amount.text().strip() else ""
        return {
            "date": format_date_boxed(self._issue_date()),
            "payee": payee,
            "amount_figures": figures,
            "amount_words": words,
            "memo": self.memo.text().strip(),
        }

    def _preview_fields(self) -> dict[str, str]:
        pad = self.pad.isChecked()
        try:
            amount = parse_amount(self.amount.text()) if self.amount.text().strip() else None
        except ValueError:
            amount = None
        if not self._is_manual_words():
            self._sync_auto_words()
        words = self._resolve_amount_words(amount, pad)
        if not words:
            words = format_amount_words(Decimal("0"), pad) if not self._is_manual_words() else ""
        return {
            "date": format_date_boxed(self._issue_date()),
            "payee": format_payee(self.payee.text() or "PAYEE NAME", pad),
            "amount_figures": format_amount_figures(amount) if amount is not None else "0.00",
            "amount_words": words or "—",
            "memo": self.memo.text().strip(),
        }

    def _refresh_preview(self) -> None:
        template = self._template()
        self.preview.set_cheque(
            template,
            self._preview_fields(),
            self._calibration(),
            self._paper_mode(),
            self._feed(),
        )

    def _on_bank_changed(self) -> None:
        self.settings["bank_id"] = self._bank_id()
        self.settings["cheque_type"] = self._cheque_type()
        save_settings(self.settings)
        self._on_form_changed()

    def _persist_form(self) -> None:
        self.settings["bank_id"] = self._bank_id()
        self.settings["cheque_type"] = self._cheque_type()
        self.settings["words_mode"] = self._words_mode()
        self.settings["pad_symbols"] = self.pad.isChecked()
        save_settings(self.settings)

    def _open_website(self) -> None:
        page = web_dir() / "index.html"
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(page)))

    def _configure_printer(self, printer: QPrinter, paper_mode: str, feed: str, template: dict) -> None:
        width_mm, height_mm = page_size_mm(paper_mode, feed, template)
        if paper_mode == "letter":
            page_size = QPageSize(QPageSize.PageSizeId.Letter)
        elif paper_mode == "a4":
            page_size = QPageSize(QPageSize.PageSizeId.A4)
        else:
            page_size = QPageSize(
                QSizeF(width_mm, height_mm),
                QPageSize.Unit.Millimeter,
                "PH Cheque",
                QPageSize.SizeMatchPolicy.ExactMatch,
            )
        layout = QPageLayout(
            page_size,
            QPageLayout.Orientation.Portrait,
            QMarginsF(0, 0, 0, 0),
            QPageLayout.Unit.Millimeter,
        )
        printer.setPageLayout(layout)
        printer.setFullPage(True)
        printer.setCopyCount(1)

    def _paint_job(self, printer: QPrinter, fields: dict[str, str], calibration: Calibration, paper_mode: str, feed: str) -> None:
        template = self._template()
        self._configure_printer(printer, paper_mode, feed, template)
        painter = QPainter(printer)
        options = DrawOptions(overlay_only=True, show_guides=False, paper_mode=paper_mode, feed=feed)
        paint_cheque(painter, template, fields, calibration, options)
        painter.end()

    def _make_printer(self) -> QPrinter:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        name = self.settings.get("printer_name")
        if name:
            printer.setPrinterName(name)
        return printer

    def _print(self) -> None:
        fields = self._field_values()
        if not fields:
            return
        if not self.payee.text().strip() or not self.amount.text().strip():
            QMessageBox.warning(self, "Cheque", "Enter a payee and an amount before printing.")
            return
        printer = self._make_printer()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return
        self.settings["printer_name"] = printer.printerName()
        self._persist_form()
        self._paint_job(printer, fields, self._calibration(), self._paper_mode(), self._feed())
        self.status.setText("Printed. Sign the cheque by hand before issuing.")

    def _print_preview(self) -> None:
        fields = self._field_values()
        if not fields:
            return
        printer = self._make_printer()
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(
            lambda p: self._paint_job(p, fields, self._calibration(), self._paper_mode(), self._feed())
        )
        preview.exec()

    def _align(self) -> None:
        dialog = AlignmentDialog(
            self,
            calibration=self._calibration(),
            paper_mode=self._paper_mode(),
            feed=self._feed(),
            on_test_print=self._alignment_test,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._refresh_preview()
            return
        cal, paper, feed = dialog.values()
        set_calibration(
            self.settings,
            self._printer_name(),
            self._bank_id(),
            cal.offset_x_mm,
            cal.offset_y_mm,
            cal.stub_width_mm,
            self._cheque_type(),
        )
        self.settings["paper_mode"] = paper
        self.settings["feed"] = feed
        self._persist_form()
        self._refresh_preview()
        self.status.setText("Alignment saved for this bank and printer.")

    def _alignment_test(self, calibration: Calibration, paper_mode: str, feed: str) -> None:
        printer = self._make_printer()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return
        self.settings["printer_name"] = printer.printerName()
        save_settings(self.settings)
        self._paint_job(printer, alignment_sample(), calibration, paper_mode, feed)
