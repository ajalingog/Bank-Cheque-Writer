"""On-screen cheque preview (guide art + overlay text)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from app.cheque_painter import Calibration, DrawOptions, page_size_mm, paint_cheque


class ChequePreview(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(640, 280)
        self._template: dict[str, Any] = {}
        self._fields: dict[str, str] = {}
        self._calibration = Calibration()
        self._options = DrawOptions(overlay_only=False, show_guides=True)

    def set_cheque(
        self,
        template: dict[str, Any],
        fields: dict[str, str],
        calibration: Calibration,
        paper_mode: str,
        feed: str,
    ) -> None:
        self._template = template
        self._fields = fields
        self._calibration = calibration
        self._options = DrawOptions(overlay_only=False, show_guides=True, paper_mode=paper_mode, feed=feed)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#d9e2d6"))
        if not self._template:
            return

        page_w, page_h = page_size_mm(self._options.paper_mode, self._options.feed, self._template)
        dpi = 160.0
        img_w = max(1, int(page_w / 25.4 * dpi))
        img_h = max(1, int(page_h / 25.4 * dpi))
        image = QImage(img_w, img_h, QImage.Format.Format_RGB32)
        image.setDotsPerMeterX(int(dpi / 0.0254))
        image.setDotsPerMeterY(int(dpi / 0.0254))
        image.fill(QColor("#ffffff"))
        img_painter = QPainter(image)
        paint_cheque(img_painter, self._template, self._fields, self._calibration, self._options)
        img_painter.end()

        margin = 16
        avail = self.rect().adjusted(margin, margin, -margin, -margin)
        scaled = image.size()
        scaled.scale(avail.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(
            avail.x() + (avail.width() - scaled.width()) / 2,
            avail.y() + (avail.height() - scaled.height()) / 2,
            scaled.width(),
            scaled.height(),
        )
        painter.drawImage(target, image)
        caption = (
            f"Print size {page_w:.1f} × {page_h:.1f} mm  "
            f"({page_w / 25.4:.2f} × {page_h / 25.4:.2f} in)  ·  PCHC cheque face, stub not included"
        )
        painter.setPen(QColor("#44554a"))
        painter.drawText(
            QRectF(avail.x(), target.bottom() + 4, avail.width(), 22),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            caption,
        )
        painter.end()
