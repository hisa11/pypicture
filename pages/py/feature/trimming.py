import cv2
import numpy as np
from PySide6.QtWidgets import QLabel, QVBoxLayout, QDialog
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QCursor
from PySide6.QtCore import Qt, QRect, QPoint

class Trimming(QDialog):
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.image = image
        self.clone = image.copy()
        self.rect = QRect()
        self.cropping = False

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width(), self.height())
        self.label.setAlignment(Qt.AlignCenter)
        self.update_image()

        # マウスカーソルを十字に設定
        self.setCursor(QCursor(Qt.CrossCursor))

    def update_image(self):
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        qimage = QImage(self.image.data, width, height,
                        bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)
        self.label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rect.setTopLeft(self.label.mapFromParent(event.pos()))
            self.rect.setBottomRight(self.label.mapFromParent(event.pos()))
            self.cropping = True

    def mouseMoveEvent(self, event):
        if self.cropping:
            self.rect.setBottomRight(self.label.mapFromParent(event.pos()))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rect.setBottomRight(self.label.mapFromParent(event.pos()))
            self.cropping = False
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.cropping:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.green, 2))
            painter.drawRect(self.rect)

    def trim(self):
        self.exec_()
        if not self.rect.isNull():
            x1 = int(self.rect.topLeft().x() /
                     self.label.width() * self.image.shape[1])
            y1 = int(self.rect.topLeft().y() /
                     self.label.height() * self.image.shape[0])
            x2 = int(self.rect.bottomRight().x() /
                     self.label.width() * self.image.shape[1])
            y2 = int(self.rect.bottomRight().y() /
                     self.label.height() * self.image.shape[0])

            # 座標が画像の範囲内に収まるように調整
            x1, x2 = sorted([max(0, min(x1, self.image.shape[1] - 1)),
                            max(0, min(x2, self.image.shape[1] - 1))])
            y1, y2 = sorted([max(0, min(y1, self.image.shape[0] - 1)),
                            max(0, min(y2, self.image.shape[0] - 1))])

            # OpenCVを使用してトリミング
            roi = self.clone[y1:y2, x1:x2]
            return roi
        return None
