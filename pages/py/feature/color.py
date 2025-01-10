import cv2
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider, QPushButton
from PySide6.QtCore import Qt, Signal

class ColorWindow(QDialog):
    color_changed = Signal(float, float, float)

    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("色調整")
        self.image = image.copy()

        self.layout = QVBoxLayout(self)

        self.label_r = QLabel("Rスケール (0～200)", self)
        self.slider_r = QSlider(Qt.Horizontal, self)
        self.slider_r.setRange(0, 200)
        self.slider_r.setValue(100)

        self.label_g = QLabel("Gスケール (0～200)", self)
        self.slider_g = QSlider(Qt.Horizontal, self)
        self.slider_g.setRange(0, 200)
        self.slider_g.setValue(100)

        self.label_b = QLabel("Bスケール (0～200)", self)
        self.slider_b = QSlider(Qt.Horizontal, self)
        self.slider_b.setRange(0, 200)
        self.slider_b.setValue(100)

        self.button_ok = QPushButton("OK", self)

        self.layout.addWidget(self.label_r)
        self.layout.addWidget(self.slider_r)
        self.layout.addWidget(self.label_g)
        self.layout.addWidget(self.slider_g)
        self.layout.addWidget(self.label_b)
        self.layout.addWidget(self.slider_b)
        self.layout.addWidget(self.button_ok)

        self.slider_r.valueChanged.connect(self.on_value_changed)
        self.slider_g.valueChanged.connect(self.on_value_changed)
        self.slider_b.valueChanged.connect(self.on_value_changed)
        self.button_ok.clicked.connect(self.accept)

    def on_value_changed(self):
        r_scale = self.slider_r.value() / 100.0
        g_scale = self.slider_g.value() / 100.0
        b_scale = self.slider_b.value() / 100.0
        self.color_changed.emit(r_scale, g_scale, b_scale)

    def get_adjusted_image(self):
        r_scale = self.slider_r.value() / 100.0
        g_scale = self.slider_g.value() / 100.0
        b_scale = self.slider_b.value() / 100.0

        bgr = list(cv2.split(self.image))
        bgr[0] = np.clip(bgr[0].astype(np.float32) *
                         b_scale, 0, 255).astype(np.uint8)
        bgr[1] = np.clip(bgr[1].astype(np.float32) *
                         g_scale, 0, 255).astype(np.uint8)
        bgr[2] = np.clip(bgr[2].astype(np.float32) *
                         r_scale, 0, 255).astype(np.uint8)
        adjusted = cv2.merge(bgr)
        return adjusted
