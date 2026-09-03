"""Draw cheque overlay in millimetres, using the paint device DPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen

PAPER_SIZES_MM = {
    "cheque": (203.2, 88.9),
    "letter": (215.9, 279.4),
    "a4": (210.0, 297.0),
}


@dataclass
class Calibration:
    offset_x_mm: float = 0.0
    offset_y_mm: float = 0.0
    stub_width_mm: float = 0.0


@dataclass
class DrawOptions:
    overlay_only: bool = True
    show_guides: bool = False
    paper_mode: str = "cheque"
    feed: str = "top_first"


def page_size_mm(paper_mode: str, feed: str, template: dict[str, Any]) -> tuple[float, float]:
    if paper_mode == "cheque":
        width = float(template.get("page_width_mm", 203.2))
        height = float(template.get("page_height_mm", 88.9))
        if feed == "left_first":
            return height, width
        return width, height
    return PAPER_SIZES_MM[paper_mode]


def _px(mm: float, dpi: float) -> float:
    return mm * dpi / 25.4


def _font(family: str, point_size: float, bold: bool = False) -> QFont:
    font = QFont(family)
    font.setPointSizeF(point_size)
    font.setBold(bold)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


def _fit_font(painter: QPainter, text: str, family: str, start_pt: float, max_width: float, bold: bool = False) -> QFont:
    size = start_pt
    font = _font(family, size, bold)
    while size > 6:
        font = _font(family, size, bold)
        metrics = QFontMetricsF(font, painter.device())
        if metrics.horizontalAdvance(text) <= max_width:
            return font
        size -= 0.5
    return font


def paint_cheque(
    painter: QPainter,
    template: dict[str, Any],
    fields: dict[str, str],
    calibration: Calibration,
    options: DrawOptions,
) -> None:
    device = painter.device()
    dpi_x = float(device.logicalDpiX())
    dpi_y = float(device.logicalDpiY())

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    cheque_w = float(template.get("page_width_mm", 203.2))
    cheque_h = float(template.get("page_height_mm", 88.9))
    origin_x = calibration.stub_width_mm + float(template.get("offset_x_mm", 0)) + calibration.offset_x_mm
    origin_y = float(template.get("offset_y_mm", 0)) + calibration.offset_y_mm

    if options.feed == "left_first" and options.paper_mode == "cheque":
        painter.translate(_px(cheque_h, dpi_x), 0)
        painter.rotate(90)

    def x_of(mm: float) -> float:
        return _px(origin_x + mm, dpi_x)

    def y_of(mm: float) -> float:
        return _px(origin_y + mm, dpi_y)

    def w_of(mm: float) -> float:
        return _px(mm, dpi_x)

    def h_of(mm: float) -> float:
        return _px(mm, dpi_y)

    if options.show_guides and not options.overlay_only:
        _draw_guides(painter, template, x_of, y_of, w_of, h_of, cheque_w, cheque_h)

    _draw_fields(painter, template, fields, x_of, y_of, w_of, h_of)
    painter.restore()


def _draw_guides(painter, template, x_of, y_of, w_of, h_of, cheque_w, cheque_h) -> None:
    brand = template.get("brand", {})
    primary = QColor(brand.get("primary", "#1f4d3a"))
    paper = QColor(brand.get("paper", "#f4f7f2"))
    box_color = QColor(brand.get("box", "#8aa090"))

    outline = QPen(primary)
    outline.setWidthF(1.2)
    painter.setPen(outline)
    painter.setBrush(paper)
    painter.drawRect(QRectF(x_of(0), y_of(0), w_of(cheque_w), h_of(cheque_h)))

    micr = float(template.get("micr_clear_mm", 16.0))
    painter.fillRect(QRectF(x_of(0), y_of(cheque_h - micr), w_of(cheque_w), h_of(micr)), paper.darker(106))

    guide = template.get("guide", {})
    painter.setPen(primary)
    painter.setFont(_font("Arial", 9, True))
    painter.drawText(QRectF(x_of(8), y_of(4), w_of(118), h_of(6)), Qt.AlignmentFlag.AlignLeft, guide.get("bank_name", ""))
    painter.setFont(_font("Arial", 7))
    painter.drawText(QRectF(x_of(8), y_of(10), w_of(118), h_of(5)), Qt.AlignmentFlag.AlignLeft, guide.get("account_name", "ACCOUNT NAME"))

    fields = template.get("fields", {})
    date = fields.get("date", {})
    figures = fields.get("amount_figures", {})
    payee = fields.get("payee", {})
    words = fields.get("amount_words", {})
    sig = fields.get("signature", {})

    painter.setPen(QColor("#6b7c70"))
    painter.setFont(_font("Arial", 6.5))
    painter.drawText(
        QRectF(x_of(payee["x_mm"]), y_of(payee["y_mm"] - 4.6), w_of(50), h_of(4)),
        Qt.AlignmentFlag.AlignLeft,
        "PAY TO THE ORDER OF",
    )
    painter.drawText(
        QRectF(x_of(date["x_mm"]), y_of(date["y_mm"] - 3.6), w_of(20), h_of(3.4)),
        Qt.AlignmentFlag.AlignLeft,
        "DATE",
    )
    painter.drawText(
        QRectF(x_of(date["x_mm"]), y_of(date["y_mm"] + date["height_mm"] + 0.3), w_of(date["width_mm"]), h_of(3.2)),
        Qt.AlignmentFlag.AlignLeft,
        "MM-DD-YYYY",
    )
    painter.drawText(
        QRectF(x_of(words["x_mm"]), y_of(words["y_mm"] - 4.2), w_of(40), h_of(3.6)),
        Qt.AlignmentFlag.AlignLeft,
        "PESOS",
    )

    box_pen = QPen(box_color)
    box_pen.setWidthF(1)
    painter.setPen(box_pen)
    painter.setBrush(QColor("#ffffff"))
    _draw_date_boxes(painter, date, x_of, y_of, w_of, h_of)
    painter.drawRect(QRectF(x_of(figures["x_mm"]), y_of(figures["y_mm"]), w_of(figures["width_mm"]), h_of(figures["height_mm"])))

    painter.setFont(_font("Arial", 8, True))
    painter.setPen(primary)
    painter.drawText(
        QRectF(x_of(figures["x_mm"] - 6), y_of(figures["y_mm"]), w_of(6), h_of(figures["height_mm"])),
        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        "P",
    )

    painter.setPen(box_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    count = int(sig.get("count", 1))
    if count <= 1:
        painter.drawRect(QRectF(x_of(sig["x_mm"]), y_of(sig["y_mm"]), w_of(sig["width_mm"]), h_of(sig["height_mm"])))
        painter.setPen(QColor("#6b7c70"))
        painter.setFont(_font("Arial", 6))
        painter.drawText(
            QRectF(x_of(sig["x_mm"]), y_of(sig["y_mm"] - 3.6), w_of(sig["width_mm"]), h_of(3.4)),
            Qt.AlignmentFlag.AlignCenter,
            "SIGNATURE",
        )
    else:
        gap = 2.0
        box_w = (float(sig["width_mm"]) - gap) / 2
        for i in range(2):
            left = float(sig["x_mm"]) + i * (box_w + gap)
            painter.setPen(box_pen)
            painter.drawRect(QRectF(x_of(left), y_of(sig["y_mm"]), w_of(box_w), h_of(sig["height_mm"])))
            painter.setPen(QColor("#6b7c70"))
            painter.setFont(_font("Arial", 6))
            painter.drawText(
                QRectF(x_of(left), y_of(sig["y_mm"] - 3.6), w_of(box_w), h_of(3.4)),
                Qt.AlignmentFlag.AlignCenter,
                f"SIGNATURE {i + 1}",
            )

    painter.setPen(QColor("#9aaa9a"))
    painter.setFont(_font("Courier New", 8))
    painter.drawText(QRectF(x_of(10), y_of(cheque_h - 12), w_of(170), h_of(6)), Qt.AlignmentFlag.AlignLeft, "c 000000000000 c 000000000 c 000000000000 c")


def _draw_date_boxes(painter, date_field, x_of, y_of, w_of, h_of) -> None:
    count = int(date_field.get("char_count", 10))
    width = float(date_field["width_mm"])
    slot = width / count
    gap = 0.4
    for i in range(count):
        painter.drawRect(
            QRectF(
                x_of(date_field["x_mm"] + i * slot + gap / 2),
                y_of(date_field["y_mm"]),
                w_of(slot - gap),
                h_of(date_field["height_mm"]),
            )
        )


def _draw_fields(painter, template, fields_data, x_of, y_of, w_of, h_of) -> None:
    layout = template.get("fields", {})
    painter.setPen(QColor("#111111"))

    date_field = layout.get("date", {})
    date_text = fields_data.get("date", "")
    if date_text:
        _draw_boxed_date(painter, date_field, date_text, x_of, y_of, w_of, h_of)

    payee_field = layout.get("payee", {})
    payee = fields_data.get("payee", "")
    if payee:
        rect = QRectF(x_of(payee_field["x_mm"]), y_of(payee_field["y_mm"]), w_of(payee_field["width_mm"]), h_of(payee_field["height_mm"]))
        font = _fit_font(painter, payee, "Arial", float(payee_field.get("font_pt", 11)), rect.width(), True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, payee)

    figures_field = layout.get("amount_figures", {})
    figures = fields_data.get("amount_figures", "")
    if figures:
        rect = QRectF(
            x_of(figures_field["x_mm"]) + 2,
            y_of(figures_field["y_mm"]),
            w_of(figures_field["width_mm"]) - 4,
            h_of(figures_field["height_mm"]),
        )
        painter.setFont(_font("Courier New", float(figures_field.get("font_pt", 12)), True))
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, figures)

    words_field = layout.get("amount_words", {})
    words = fields_data.get("amount_words", "")
    if words:
        rect = QRectF(x_of(words_field["x_mm"]), y_of(words_field["y_mm"]), w_of(words_field["width_mm"]), h_of(words_field["height_mm"]))
        font = _fit_font(painter, words, "Arial", float(words_field.get("font_pt", 9)), rect.width())
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, words)

    memo_field = layout.get("memo", {})
    memo = fields_data.get("memo", "")
    if memo:
        rect = QRectF(x_of(memo_field["x_mm"]), y_of(memo_field["y_mm"]), w_of(memo_field["width_mm"]), h_of(memo_field["height_mm"]))
        painter.setFont(_font("Arial", float(memo_field.get("font_pt", 9))))
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, memo)


def _draw_boxed_date(painter, date_field, text: str, x_of, y_of, w_of, h_of) -> None:
    count = int(date_field.get("char_count", 10))
    padded = (text + " " * count)[:count]
    width = float(date_field["width_mm"])
    slot = width / count
    font = _font("Courier New", float(date_field.get("font_pt", 11)), True)
    painter.setFont(font)
    for i, ch in enumerate(padded):
        rect = QRectF(
            x_of(date_field["x_mm"] + i * slot),
            y_of(date_field["y_mm"]),
            w_of(slot),
            h_of(date_field["height_mm"]),
        )
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, ch)
