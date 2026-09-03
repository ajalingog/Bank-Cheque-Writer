"""Per-printer / per-bank millimetre calibration and alignment test print."""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.cheque_painter import Calibration


class AlignmentDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        calibration: Calibration,
        paper_mode: str,
        feed: str,
        on_test_print: Callable[[Calibration, str, str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fix cheque alignment")
        self.setModal(True)
        self._on_test_print = on_test_print
        self.setMinimumWidth(480)

        intro = QLabel(
            "Do this once per bank and printer.\n\n"
            "1. Load a photocopy or spare cheque.\n"
            "2. Print the alignment test.\n"
            "3. Nudge Move right / Move down until text sits in the boxes.\n"
            "4. Click Save. Offsets are remembered for this bank and printer."
        )
        intro.setWordWrap(True)

        self.offset_x = QDoubleSpinBox()
        self.offset_y = QDoubleSpinBox()
        self.stub = QDoubleSpinBox()
        for spin in (self.offset_x, self.offset_y, self.stub):
            spin.setDecimals(1)
            spin.setSingleStep(0.1)
            spin.setRange(-80.0, 80.0)
            spin.setSuffix(" mm")
        self.stub.setRange(0.0, 120.0)
        self.offset_x.setValue(calibration.offset_x_mm)
        self.offset_y.setValue(calibration.offset_y_mm)
        self.stub.setValue(calibration.stub_width_mm)

        self.paper = QComboBox()
        self.paper.addItem("Cheque size (7.5 × 3.5 in)", "cheque")
        self.paper.addItem("Letter, cheque at top-left", "letter")
        self.paper.addItem("A4, cheque at top-left", "a4")
        idx = self.paper.findData(paper_mode)
        if idx >= 0:
            self.paper.setCurrentIndex(idx)

        self.feed = QComboBox()
        self.feed.addItem("Top of cheque enters printer first", "top_first")
        self.feed.addItem("Left edge of cheque enters printer first", "left_first")
        idx = self.feed.findData(feed)
        if idx >= 0:
            self.feed.setCurrentIndex(idx)

        form = QFormLayout()
        form.addRow("Move right (X)", self.offset_x)
        form.addRow("Move down (Y)", self.offset_y)
        form.addRow("Left stub width", self.stub)
        form.addRow("Paper", self.paper)
        form.addRow("Feed", self.feed)

        test_btn = QPushButton("Print alignment test")
        test_btn.clicked.connect(self._test)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        row = QHBoxLayout()
        row.addWidget(test_btn)
        row.addStretch()
        layout.addLayout(row)
        layout.addWidget(buttons)
        self.resize(460, 320)

    def values(self) -> tuple[Calibration, str, str]:
        cal = Calibration(
            offset_x_mm=self.offset_x.value(),
            offset_y_mm=self.offset_y.value(),
            stub_width_mm=self.stub.value(),
        )
        return cal, self.paper.currentData(), self.feed.currentData()

    def _test(self) -> None:
        if self._on_test_print:
            cal, paper, feed = self.values()
            self._on_test_print(cal, paper, feed)
