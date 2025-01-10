import cv2
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QSlider, QSpinBox, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

class RevolutionWindow(QDialog):
    angle_changed = Signal(int)

    def __init__(self, image, parent=None):
        super(RevolutionWindow, self).__init__(parent)
        self.original_image = image.copy()
        self.rotated_image = image.copy()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("画像の回転")
        self.layout = QVBoxLayout()

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(-180)
        self.slider.setMaximum(180)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.rotate_image)

        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(-180)
        self.spin_box.setMaximum(180)
        self.spin_box.setValue(0)
        self.spin_box.valueChanged.connect(self.rotate_image)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.spin_box)
        self.layout.addLayout(slider_layout)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def rotate_image(self, angle):
        if isinstance(angle, int):
            self.slider.setValue(angle)
            self.spin_box.setValue(angle)
        # "+" のangleは時計回り(右回転)とする
        center = (self.original_image.shape[1] // 2,
                  self.original_image.shape[0] // 2)
        matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        self.rotated_image = cv2.warpAffine(
            self.original_image, matrix,
            (self.original_image.shape[1], self.original_image.shape[0])
        )
        self.angle_changed.emit(angle)

    def get_rotated_image(self):
        return self.rotated_image
