import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QSpinBox, QColorDialog)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Signal, Qt

class TextWindow(QDialog):
    text_applied = Signal(str, QFont, QColor, int)

    def __init__(self, parent=None):
        super(TextWindow, self).__init__(parent)
        self.setWindowTitle("テキスト設定")
        self.main_layout = QVBoxLayout(self)

        # フォント選択
        self.font_combo = QComboBox(self)
        self.font_combo.addItems(
            ["Arial", "Times New Roman", "MS Gothic", "MS Mincho", "Yu Gothic"])
        # フォントサイズ
        self.size_spin = QSpinBox(self)
        self.size_spin.setRange(8, 100)
        self.size_spin.setValue(24)
        # 色選択
        self.color_btn = QPushButton("色選択", self)
        self.color_btn.clicked.connect(self.on_color_select)
        self.selected_color = QColor(0, 0, 0)

        # テキスト入力完了用ボタン
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.apply_settings)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("フォント:"))
        hl.addWidget(self.font_combo)
        hl.addWidget(QLabel("サイズ:"))
        hl.addWidget(self.size_spin)
        hl.addWidget(self.color_btn)

        self.main_layout.addLayout(hl)
        self.main_layout.addWidget(self.ok_button)

    def on_color_select(self):
        c = QColorDialog.getColor(self.selected_color, self, "フォント色を選択")
        if c.isValid():
            self.selected_color = c

    def apply_settings(self):
        font = QFont(self.font_combo.currentText(), self.size_spin.value())
        self.text_applied.emit(
            "", font, self.selected_color, self.size_spin.value())
        self.accept()
