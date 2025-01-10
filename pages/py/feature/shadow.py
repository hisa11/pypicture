import cv2
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QSlider, QSpinBox, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

class ShadowWindow(QDialog):
    shadow_changed = Signal(int)

    def __init__(self, image, parent=None):
        super(ShadowWindow, self).__init__(parent)
        self.original_image = image.copy()
        self.adjusted_image = image.copy()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("影の調整")
        self.layout = QVBoxLayout()

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.adjust_shadow)

        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(0)
        self.spin_box.setMaximum(100)
        self.spin_box.setValue(0)
        self.spin_box.valueChanged.connect(self.adjust_shadow)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.spin_box)
        self.layout.addLayout(slider_layout)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def adjust_shadow(self, value):
        if isinstance(value, int):
            self.slider.setValue(value)
            self.spin_box.setValue(value)

        # 影の強さを調整
        shadow_strength = value / 100.0
        shadow = np.zeros_like(self.original_image)
        shadow[:, :, 0] = self.original_image[:, :, 0] * (1 - shadow_strength)
        shadow[:, :, 1] = self.original_image[:, :, 1] * (1 - shadow_strength)
        shadow[:, :, 2] = self.original_image[:, :, 2] * (1 - shadow_strength)
        self.adjusted_image = cv2.addWeighted(
            self.original_image, 1, shadow, shadow_strength, 0)

        self.shadow_changed.emit(value)

    def get_adjusted_image(self):
        return self.adjusted_image
