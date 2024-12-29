import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QDialog
from PySide6.QtGui import QPixmap, QImage, QWheelEvent, QPainter, QPen, QCursor
from PySide6.QtCore import Qt, QRect
from picture import Ui_MainWindow
from revolution import RevolutionWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.image_label = QLabel(self.ui.frame)
        self.image_label.setGeometry(
            0, 0, self.ui.frame.width(), self.ui.frame.height())
        self.image_label.setAlignment(Qt.AlignCenter)

        self.history_layout = QVBoxLayout(self.ui.frame)
        self.history_layout.addWidget(self.image_label)

        self.scale_factor = 1.0
        self.image = None
        self.display_image_cache = None
        self.cropping = False
        self.rect = QRect()
        self.original_scale_factor = 1.0

        self.ui.trimming.clicked.connect(self.start_trimming)
        self.ui.revolution.clicked.connect(self.open_revolution_window)

    def set_image(self, image, fit_to_frame=True):
        self.image = np.ascontiguousarray(image)
        self.scale_factor = 1.0
        self.display_image_cache = None
        if fit_to_frame:
            self.fit_image_to_frame()
        else:
            self.display_image()

    def fit_image_to_frame(self):
        if self.image is None:
            return
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        qimage = QImage(self.image.data, width, height,
                        bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)
        label_width = self.ui.frame.width()
        label_height = self.ui.frame.height()
        scale_factor = min(label_width / pixmap.width(),
                           label_height / pixmap.height())
        new_width = int(pixmap.width() * scale_factor)
        new_height = int(pixmap.height() * scale_factor)
        pixmap = pixmap.scaled(new_width, new_height,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.setGeometry((label_width - new_width) // 2,
                                     (label_height - new_height) // 2,
                                     new_width, new_height)

    def display_image(self):
        if self.image is None:
            return
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        qimage = QImage(self.image.data, width, height,
                        bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)
        self.image_label.setPixmap(pixmap)
        self.image_label.setGeometry(0, 0, width, height)

    def update_image(self):
        if self.image is None:
            return
        if self.display_image_cache is None:
            height, width, channel = self.image.shape
            bytes_per_line = 3 * width
            qimage = QImage(self.image.data, width, height,
                            bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(qimage)
            self.display_image_cache = pixmap
        new_width = int(self.display_image_cache.width() * self.scale_factor)
        new_height = int(self.display_image_cache.height() * self.scale_factor)
        pixmap = self.display_image_cache.scaled(
            new_width, new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)
        self.image_label.setGeometry(
            (self.ui.frame.width() - new_width) // 2,
            (self.ui.frame.height() - new_height) // 2,
            new_width, new_height
        )

    def wheelEvent(self, event: QWheelEvent):
        if self.image is None:
            return
        if event.angleDelta().y() > 0:
            self.scale_factor = min(self.scale_factor * 1.1, 5.0)
        else:
            self.scale_factor = max(self.scale_factor / 1.1, 0.2)
        self.update_image()

    def start_trimming(self):
        if self.image is None:
            return
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.cropping = True
        self.original_scale_factor = self.scale_factor
        self.scale_factor = 1.0
        self.update_image()

    def mousePressEvent(self, event):
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            self.rect.setTopLeft(self.image_label.mapFromParent(event.pos()))
            self.rect.setBottomRight(
                self.image_label.mapFromParent(event.pos())
            )

    def mouseMoveEvent(self, event):
        if self.cropping:
            self.rect.setBottomRight(
                self.image_label.mapFromParent(event.pos())
            )
            self.update()

    def mouseReleaseEvent(self, event):
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            self.rect.setBottomRight(
                self.image_label.mapFromParent(event.pos())
            )
            self.cropping = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            # トリミング処理が必要ならここで実行:
            # self.crop_image()
            # self.scale_factor = self.original_scale_factor
            # self.update_image()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.cropping:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine))
            painter.drawRect(self.rect)

    def open_revolution_window(self):
        if self.image is None:
            return
        revolution_window = RevolutionWindow(self.image, self)
        revolution_window.angle_changed.connect(self.update_rotated_image)
        if revolution_window.exec_() == QDialog.Accepted:
            self.set_image(revolution_window.get_rotated_image(),
                           fit_to_frame=False)

    def update_rotated_image(self, angle):
        rw = self.sender()
        if rw:
            updated = rw.get_rotated_image()
            self.set_image(updated, fit_to_frame=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
