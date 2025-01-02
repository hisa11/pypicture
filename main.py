import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QDialog
from PySide6.QtGui import QPixmap, QImage, QWheelEvent, QPainter, QPen, QCursor
from PySide6.QtCore import Qt, QRect
from picture import Ui_MainWindow
from revolution import RevolutionWindow
from brightness import BrightnessWindow
from contrast import ContrastWindow
from shadow import ShadowWindow
from chroma import ChromaWindow
from color import ColorWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # マウス追跡を有効化
        self.setMouseTracking(True)
        self.ui.frame.setMouseTracking(True)

        # 画像表示用ラベル
        self.image_label = QLabel(self.ui.frame)
        self.image_label.setGeometry(
            0, 0, self.ui.frame.width(), self.ui.frame.height())
        self.image_label.setAlignment(Qt.AlignCenter)
        # マウスイベントをメインウィンドウで受け取るために透過設定
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.history_layout = QVBoxLayout(self.ui.frame)
        self.history_layout.addWidget(self.image_label)

        self.image = None
        self.display_image_cache = None

        self.user_scale_factor = 1.0
        self.base_scale_factor = 1.0

        # トリミング用
        self.cropping = False
        self.rect = QRect()

        # パン操作用変数
        self.is_panning = False
        self.last_pan_pos = None
        self.pan_offset_x = 0
        self.pan_offset_y = 0

        # ボタンイベント
        self.ui.trimming.clicked.connect(self.start_trimming)
        self.ui.revolution.clicked.connect(self.open_revolution_window)
        self.ui.brightness.clicked.connect(self.open_brightness_window)
        self.ui.contrast.clicked.connect(self.open_contrast_window)
        self.ui.shadow.clicked.connect(self.open_shadow_window)
        self.ui.chroma.clicked.connect(self.open_chroma_window)
        self.ui.color.clicked.connect(self.open_color_window)

    def set_image(self, image, fit_to_frame=True):
        self.image = np.ascontiguousarray(image)
        self.display_image_cache = None
        if fit_to_frame:
            self.calc_base_scale_factor()
            self.user_scale_factor = 1.0
            self.pan_offset_x = 0
            self.pan_offset_y = 0
        self.update_image()

    def calc_base_scale_factor(self):
        if self.image is None:
            self.base_scale_factor = 1.0
            return
        h, w, _ = self.image.shape
        qimg = QImage(self.image.data, w, h, w * 3,
                      QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimg)
        frame_w = self.ui.frame.width()
        frame_h = self.ui.frame.height()
        scale_fit = min(frame_w / pixmap.width(), frame_h / pixmap.height())
        if scale_fit < 1.0:
            self.base_scale_factor = scale_fit
        else:
            self.base_scale_factor = 1.0

    def update_image(self):
        if self.image is None:
            return
        if self.display_image_cache is None:
            h, w, _ = self.image.shape
            qimg = QImage(self.image.data, w, h, w * 3,
                          QImage.Format_RGB888).rgbSwapped()
            self.display_image_cache = QPixmap.fromImage(qimg)

        final_scale = self.base_scale_factor * self.user_scale_factor
        # 最大ズーム倍率を制限
        if final_scale > 5.0:
            final_scale = 5.0
            self.user_scale_factor = final_scale / self.base_scale_factor

        new_width = int(self.display_image_cache.width() * final_scale)
        new_height = int(self.display_image_cache.height() * final_scale)
        scaled_pixmap = self.display_image_cache.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        fw = self.ui.frame.width()
        fh = self.ui.frame.height()

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setGeometry(
            (fw - new_width) // 2 + self.pan_offset_x,
            (fh - new_height) // 2 + self.pan_offset_y,
            new_width,
            new_height
        )

    def wheelEvent(self, event: QWheelEvent):
        if self.image is None:
            return
        if event.angleDelta().y() > 0:
            self.user_scale_factor *= 1.1
        else:
            self.user_scale_factor /= 1.1
        self.update_image()

    def mousePressEvent(self, event):
        if self.image is None:
            return

        # 左または中クリックでパン開始
        if not self.cropping and event.button() in [Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton]:
            self.is_panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))

        # トリミング開始
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            mapped_pos = self.image_label.mapFromParent(event.pos())
            self.rect.setTopLeft(mapped_pos)
            self.rect.setBottomRight(mapped_pos)

    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_pan_pos and not self.cropping:
            dx = event.pos().x() - self.last_pan_pos.x()
            dy = event.pos().y() - self.last_pan_pos.y()
            self.pan_offset_x += dx
            self.pan_offset_y += dy
            self.last_pan_pos = event.pos()
            self.update_image()
        elif self.cropping:
            mapped_pos = self.image_label.mapFromParent(event.pos())
            self.rect.setBottomRight(mapped_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_panning and event.button() in [Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton]:
            self.is_panning = False
            self.setCursor(QCursor(Qt.ArrowCursor))
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            mapped_pos = self.image_label.mapFromParent(event.pos())
            self.rect.setBottomRight(mapped_pos)
            self.cropping = False
            self.setCursor(QCursor(Qt.ArrowCursor))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.cropping:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.green, 2, Qt.DashLine))
            painter.drawRect(self.rect)

    def start_trimming(self):
        if self.image is None:
            return
        self.cropping = True
        self.setCursor(QCursor(Qt.CrossCursor))

    def open_revolution_window(self):
        if self.image is None:
            return
        rev = RevolutionWindow(self.image, self)
        rev.angle_changed.connect(self.update_rotated_image)
        if rev.exec_() == QDialog.Accepted:
            self.set_image(rev.get_rotated_image(), fit_to_frame=False)

    def update_rotated_image(self, angle):
        rw = self.sender()
        if rw:
            rotated = rw.get_rotated_image()
            self.image = rotated
            self.display_image_cache = None
            self.update_image()

    def open_brightness_window(self):
        if self.image is None:
            return
        brightness_window = BrightnessWindow(self.image, self)
        brightness_window.brightness_changed.connect(
            self.update_brightness_image)
        if brightness_window.exec_() == QDialog.Accepted:
            self.set_image(brightness_window.get_adjusted_image(),
                           fit_to_frame=False)

    def update_brightness_image(self, value):
        bw = self.sender()
        if bw:
            adjusted = bw.get_adjusted_image()
            self.image = adjusted
            self.display_image_cache = None
            self.update_image()

    def open_contrast_window(self):
        if self.image is None:
            return
        contrast_window = ContrastWindow(self.image, self)
        contrast_window.contrast_changed.connect(self.update_contrast_image)
        if contrast_window.exec_() == QDialog.Accepted:
            self.set_image(contrast_window.get_adjusted_image(),
                           fit_to_frame=False)

    def update_contrast_image(self, value):
        cw = self.sender()
        if cw:
            adjusted = cw.get_adjusted_image()
            self.image = adjusted
            self.display_image_cache = None
            self.update_image()

    def open_shadow_window(self):
        if self.image is None:
            return
        shadow_window = ShadowWindow(self.image, self)
        shadow_window.shadow_changed.connect(self.update_shadow_image)
        if shadow_window.exec_() == QDialog.Accepted:
            self.set_image(shadow_window.get_adjusted_image(),
                           fit_to_frame=False)

    def update_shadow_image(self, value):
        sw = self.sender()
        if sw:
            adjusted = sw.get_adjusted_image()
            self.image = adjusted
            self.display_image_cache = None
            self.update_image()

    def open_chroma_window(self):
        if self.image is None:
            return
        chroma_window = ChromaWindow(self.image, self)
        chroma_window.chroma_changed.connect(self.update_chroma_image)
        if chroma_window.exec_() == QDialog.Accepted:
            self.set_image(chroma_window.get_adjusted_image(),
                           fit_to_frame=False)

    def update_chroma_image(self, value):
        cw = self.sender()
        if cw:
            adjusted = cw.get_adjusted_image()
            self.image = adjusted
            self.display_image_cache = None
            self.update_image()

    def open_color_window(self):
        if self.image is None:
            return
        color_window = ColorWindow(self.image, self)
        color_window.color_changed.connect(self.update_color_image)
        if color_window.exec_() == QDialog.Accepted:
            # OKボタン時のみ自画像を更新
            final_image = color_window.get_adjusted_image()
            self.set_image(final_image, fit_to_frame=False)

    def update_color_image(self, r_scale, g_scale, b_scale):
        if self.image is None:
            return
        # リアルタイムプレビュー (self.image は上書きしない)
        original = self.image.copy()
        temp_bgr = list(cv2.split(original))
        temp_bgr[0] = np.clip(temp_bgr[0].astype(
            np.float32) * b_scale, 0, 255).astype(np.uint8)
        temp_bgr[1] = np.clip(temp_bgr[1].astype(
            np.float32) * g_scale, 0, 255).astype(np.uint8)
        temp_bgr[2] = np.clip(temp_bgr[2].astype(
            np.float32) * r_scale, 0, 255).astype(np.uint8)
        preview = cv2.merge(temp_bgr)

        # 直接プレビューのみ表示 (display_image_cache や self.image は更新しない)
        h, w, _ = preview.shape
        qimg = QImage(preview.data, w, h, w * 3,
                      QImage.Format_RGB888).rgbSwapped()
        pixmap_preview = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap_preview)

        # 現在の拡大率を維持して更新
        self.image_label.setGeometry(
            (self.ui.frame.width() - pixmap_preview.width()) // 2 + self.pan_offset_x,
            (self.ui.frame.height() - pixmap_preview.height()) // 2 + self.pan_offset_y,
            pixmap_preview.width(),
            pixmap_preview.height()
        )

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
