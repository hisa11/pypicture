import cv2
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider, QPushButton
from PySide6.QtCore import Qt, Signal

class ChromaWindow(QDialog):
    chroma_changed = Signal(float)

    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("彩度調整")
        self.image = image.copy()

        self.layout = QVBoxLayout(self)

        self.label_info = QLabel("彩度を調整してください (0～200)", self)
        self.layout.addWidget(self.label_info)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(200)
        self.slider.setValue(100)
        self.layout.addWidget(self.slider)

        self.button_ok = QPushButton("OK", self)
        self.layout.addWidget(self.button_ok)

        # スライダー値変更時にシグナルを発行
        self.slider.valueChanged.connect(self.on_slider_value_changed)

        # OKボタンが押されたらダイアログを閉じる
        self.button_ok.clicked.connect(self.accept)

    def on_slider_value_changed(self):
        # スライダーの値（0～200）を0.0～2.0に変換
        scale = self.slider.value() / 100.0
        self.chroma_changed.emit(scale)

    def get_adjusted_image(self):
        # 現在のスライダー値を取得して画像を調整
        scale = self.slider.value() / 100.0
        # OpenCVで彩度を調整: BGR -> HSV -> Sチャンネルスケール -> BGR
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] *= scale
        # 範囲外をクリップしておく
        hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)
        hsv = hsv.astype(np.uint8)
        adjusted = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return adjusted
