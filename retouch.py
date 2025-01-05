import cv2
import numpy as np
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QMessageBox, QRadioButton, QButtonGroup
from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap, QImage
import os

class RetouchWindow(QDialog):
    retouch_completed = Signal(np.ndarray)

    def __init__(self, image, parent=None):
        super(RetouchWindow, self).__init__(parent)
        self.setWindowTitle("顔レタッチ")
        self.setFixedSize(200, 150)
        self.image = image

        layout = QVBoxLayout(self)

        # モザイクの選択ボタンを追加
        self.mosaic_radio = QRadioButton("モザイク")
        self.mosaic_radio.setChecked(True)  # デフォルトでモザイクを選択

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.mosaic_radio)

        layout.addWidget(self.mosaic_radio)

        self.retouch_button = QPushButton("顔をレタッチ")
        self.retouch_button.clicked.connect(self.retouch_faces)
        layout.addWidget(self.retouch_button)

    def retouch_faces(self):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        cascade_path = './haarcascade_frontalface_default.xml'  # 正しいパスに変更
        face_cascade = cv2.CascadeClassifier(cascade_path)

        # カスケード分類器のロード確認
        if face_cascade.empty():
            QMessageBox.critical(
                self, "エラー", f"カスケードファイルをロードできませんでした: {cascade_path}")
            return

        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) == 0:
            QMessageBox.information(self, "情報", "顔が見つかりませんでした。")
            return

        for (x, y, w, h) in faces:
            face_roi = self.image[y:y + h, x:x + w]
            if self.mosaic_radio.isChecked():
                # モザイクを適用
                face_roi = cv2.resize(face_roi, (w // 10, h // 10))  # モザイクの範囲を大きく
                face_roi = cv2.resize(
                    face_roi, (w, h), interpolation=cv2.INTER_NEAREST)
            self.image[y:y + h, x:x + w] = face_roi

        QMessageBox.information(self, "完了", f"{len(faces)}つの顔をレタッチしました。")
        self.retouch_completed.emit(self.image)
        self.accept()
