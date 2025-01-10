import cv2
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QSlider, QSpinBox, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

class ContrastWindow(QDialog):
    contrast_changed = Signal(int)

    def __init__(self, image, parent=None):
        super(ContrastWindow, self).__init__(parent)
        self.original_image = image.copy()
        self.adjusted_image = image.copy()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("コントラスト調整")
        self.layout = QVBoxLayout()

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.adjust_contrast)

        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(-100)
        self.spin_box.setMaximum(100)
        self.spin_box.setValue(0)
        self.spin_box.valueChanged.connect(self.adjust_contrast)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.spin_box)
        self.layout.addLayout(slider_layout)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def adjust_contrast(self, value):
        if isinstance(value, int):
            self.slider.setValue(value)
            self.spin_box.setValue(value)

        # α:コントラスト係数 (1.0 + value/100)
        # ピクセルを(ピクセル - 127.5)*α + 127.5で変換
        alpha = 1.0 + (value / 100.0)
        table = np.arange(256, dtype=np.float32)
        table = (table - 127.5) * alpha + 127.5
        table = np.clip(table, 0, 255).astype(np.uint8)
        self.adjusted_image = cv2.LUT(self.original_image, table)

        self.contrast_changed.emit(value)

    def get_adjusted_image(self):
        return self.adjusted_image
