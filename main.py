import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QDialog, QFileDialog,
    QMessageBox
)
from PySide6.QtGui import (
    QPixmap, QImage, QWheelEvent, QPainter, QPen, QCursor,
    QFont, QColor, QFontMetrics
)
from PySide6.QtCore import Qt, QRect, QPoint, QSize

from picture import Ui_MainWindow
from revolution import RevolutionWindow
from brightness import BrightnessWindow
from contrast import ContrastWindow
from shadow import ShadowWindow
from chroma import ChromaWindow
from color import ColorWindow
from text import TextWindow
from sticker import StickerWindow
from retouch import RetouchWindow
from save import SaveWindow  

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setMouseTracking(True)
        self.ui.frame.setMouseTracking(True)

        self.image_label = QLabel(self.ui.frame)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.history_layout = QVBoxLayout(self.ui.frame)
        self.history_layout.addWidget(self.image_label)

        self.image = None
        self.display_image_cache = None

        self.user_scale_factor = 1.0
        self.base_scale_factor = 1.0
        self.cropping = False
        self.rect = QRect()

        self.is_panning = False
        self.last_pan_pos = None
        self.pan_offset_x = 0
        self.pan_offset_y = 0

        # テキスト編集
        self.text_editing = False
        self.temp_text = ""
        self.temp_text_pos = QPoint(0, 0)
        self.temp_font = QFont()
        self.temp_color = QColor(0, 0, 0)
        self.text_dragging = False

        # ステッカー編集
        self.sticker_editing = False
        self.temp_sticker = QPixmap()
        self.temp_sticker_pos = QPoint(0, 0)
        self.sticker_dragging = False
        self.sticker_scaling = False
        self.temp_sticker_scale = 1.0
        self.scale_handle_rect = QRect()
        self.scale_handle_size = 20

        # ボタン
        self.ui.trimming.clicked.connect(self.start_trimming)
        self.ui.revolution.clicked.connect(self.open_revolution_window)
        self.ui.brightness.clicked.connect(self.open_brightness_window)
        self.ui.contrast.clicked.connect(self.open_contrast_window)
        self.ui.shadow.clicked.connect(self.open_shadow_window)
        self.ui.chroma.clicked.connect(self.open_chroma_window)
        self.ui.color.clicked.connect(self.open_color_window)
        self.ui.text.clicked.connect(self.open_text_window)
        self.ui.sticker.clicked.connect(self.open_sticker_window)
        self.ui.retouch.clicked.connect(self.open_retouch_window)
        self.ui.save.clicked.connect(self.open_save_window)  # 追加

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()
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
        self.base_scale_factor = scale_fit if scale_fit < 1.0 else 1.0

    def update_image(self):
        if self.image is None:
            return
        if self.display_image_cache is None:
            h, w, _ = self.image.shape
            qimg = QImage(self.image.data, w, h, w * 3,
                          QImage.Format_RGB888).rgbSwapped()
            self.display_image_cache = QPixmap.fromImage(qimg)

        final_scale = self.base_scale_factor * self.user_scale_factor
        if final_scale > 5.0:
            final_scale = 5.0
            self.user_scale_factor = final_scale / self.base_scale_factor

        new_width = int(self.display_image_cache.width() * final_scale)
        new_height = int(self.display_image_cache.height() * final_scale)
        scaled_pixmap = self.display_image_cache.scaled(
            new_width, new_height,
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
        self.update()

    def open_save_window(self):
        if self.image is None:
            QMessageBox.warning(self, "警告", "画像がロードされていません。")
            return
        save_window = SaveWindow(self)
        save_window.save_completed.connect(self.save_image)
        save_window.exec_()

    def save_image(self, file_path, quality):
        if self.image is None:
            QMessageBox.warning(self, "警告", "画像がロードされていません。")
            return
        extension = file_path.split('.')[-1].lower()
        if extension == 'jpg' or extension == 'jpeg':
            cv2.imwrite(file_path, self.image, [
                        int(cv2.IMWRITE_JPEG_QUALITY), quality])
        else:
            cv2.imwrite(file_path, self.image)
        QMessageBox.information(self, "完了", "画像が保存されました。")


    def mousePressEvent(self, event):
        # テキスト編集
        if self.text_editing:
            if self.temp_text:
                text_rect = self.get_text_rect()
                click_pos = event.pos() - self.image_label.pos()
                if text_rect.contains(click_pos):
                    self.text_dragging = True
                    self.last_pan_pos = event.pos()
                else:
                    self.temp_text_pos = click_pos
            return

        # ステッカー編集
        if self.sticker_editing and not self.temp_sticker.isNull():
            click_pos = event.pos() - self.image_label.pos()
            scaled_width = self.temp_sticker.width() * self.temp_sticker_scale
            scaled_height = self.temp_sticker.height() * self.temp_sticker_scale
            sticker_rect = QRect(self.temp_sticker_pos,
                                 QSize(scaled_width, scaled_height))

            if self.scale_handle_rect.contains(click_pos):
                self.sticker_scaling = True
                self.last_pan_pos = event.pos()
                return
            elif sticker_rect.contains(click_pos):
                self.sticker_dragging = True
                self.last_pan_pos = event.pos()
                return

        # 通常処理(パン/トリミング)
        if self.image is None:
            return
        if not self.cropping and event.button() in [Qt.LeftButton, Qt.MiddleButton]:
            self.is_panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        if self.cropping and event.button() == Qt.LeftButton:
            mapped_pos = self.image_label.mapFromParent(event.pos())
            self.rect.setTopLeft(mapped_pos)
            self.rect.setBottomRight(mapped_pos)

    def mouseMoveEvent(self, event):
        # テキストドラッグ
        if self.text_dragging and self.text_editing and self.last_pan_pos:
            dx = event.pos().x() - self.last_pan_pos.x()
            dy = event.pos().y() - self.last_pan_pos.y()
            self.temp_text_pos += QPoint(dx, dy)
            self.last_pan_pos = event.pos()
            self.update()
            return

        # ステッカードラッグ
        if self.sticker_dragging and self.sticker_editing and self.last_pan_pos:
            dx = event.pos().x() - self.last_pan_pos.x()
            dy = event.pos().y() - self.last_pan_pos.y()
            self.temp_sticker_pos += QPoint(dx, dy)
            self.temp_sticker_pos.setX(
                max(0, min(self.temp_sticker_pos.x(), self.ui.frame.width() - self.temp_sticker.width() * self.temp_sticker_scale)))
            self.temp_sticker_pos.setY(
                max(0, min(self.temp_sticker_pos.y(), self.ui.frame.height() - self.temp_sticker.height() * self.temp_sticker_scale)))
            self.last_pan_pos = event.pos()
            self.update()
            return

        # ステッカーリサイズ
        if self.sticker_scaling and self.sticker_editing and self.last_pan_pos:
            dx = event.pos().x() - self.last_pan_pos.x()
            dy = event.pos().y() - self.last_pan_pos.y()
            scale_change = (dx + dy) * 0.005
            self.temp_sticker_scale = max(
                0.1, self.temp_sticker_scale + scale_change)
            self.last_pan_pos = event.pos()
            self.update()
            return

        # パン/トリミング
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
        
        if self.text_dragging and event.button() == Qt.LeftButton:
            self.text_dragging = False

        
        if self.sticker_dragging and event.button() == Qt.LeftButton:
            self.sticker_dragging = False
        if self.sticker_scaling and event.button() == Qt.LeftButton:
            self.sticker_scaling = False

        
        if self.is_panning and event.button() in [Qt.LeftButton, Qt.MiddleButton]:
            self.is_panning = False
            self.setCursor(QCursor(Qt.ArrowCursor))

        
        if self.cropping and event.button() == Qt.LeftButton:
            mapped_pos = self.image_label.mapFromParent(event.pos())
            self.rect.setBottomRight(mapped_pos)
            self.cropping = False
            self.setCursor(QCursor(Qt.ArrowCursor))

    def wheelEvent(self, event: QWheelEvent):
        if self.image is None:
            return
        if event.angleDelta().y() > 0:
            self.user_scale_factor *= 1.1
        else:
            self.user_scale_factor /= 1.1
        self.update_image()

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

    def open_retouch_window(self):
        if self.image is None:
            QMessageBox.warning(self, "警告", "画像がロードされていません。")
            return
        retouch_window = RetouchWindow(self.image, self)
        retouch_window.retouch_completed.connect(self.set_image)
        retouch_window.exec_()

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
            final_image = color_window.get_adjusted_image()
            self.set_image(final_image, fit_to_frame=False)

    def update_color_image(self, r_scale, g_scale, b_scale):
        if self.image is None:
            return
        original = self.image.copy()
        temp_bgr = list(cv2.split(original))
        temp_bgr[0] = np.clip(temp_bgr[0].astype(
            np.float32) * b_scale, 0, 255).astype(np.uint8)
        temp_bgr[1] = np.clip(temp_bgr[1].astype(
            np.float32) * g_scale, 0, 255).astype(np.uint8)
        temp_bgr[2] = np.clip(temp_bgr[2].astype(
            np.float32) * r_scale, 0, 255).astype(np.uint8)
        preview = cv2.merge(temp_bgr)

        h, w, _ = preview.shape
        qimg = QImage(preview.data, w, h, w * 3,
                      QImage.Format_RGB888).rgbSwapped()
        pixmap_preview = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap_preview)
        self.image_label.setGeometry(
            (self.ui.frame.width() - pixmap_preview.width()) // 2 + self.pan_offset_x,
            (self.ui.frame.height() - pixmap_preview.height()) // 2 + self.pan_offset_y,
            pixmap_preview.width(),
            pixmap_preview.height()
        )

    def open_text_window(self):
        if self.image is None:
            return
        self.text_editing = True
        tw = TextWindow(self)
        tw.text_applied.connect(self.on_text_settings_applied)
        tw.exec_()

    def on_text_settings_applied(self, text, font, color, size):
        self.temp_text = text
        self.temp_font = font
        self.temp_color = color
        self.text_editing = True
        self.update()

    def get_text_rect(self):
        fm = QFontMetrics(self.temp_font)
        width = fm.horizontalAdvance(self.temp_text)
        height = fm.height()
        return QRect(self.temp_text_pos, QSize(width, height))

    def confirm_text(self):
        if not self.temp_text:
            return
        h, w, _ = self.image.shape
        img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        cv_img = QImage(img_rgb.data, w, h, w * 3, QImage.Format_RGB888)
        px = QPixmap.fromImage(cv_img)

        p = QPainter(px)
        p.setFont(self.temp_font)
        p.setPen(self.temp_color)
        p.drawText(self.temp_text_pos, self.temp_text)
        p.end()

        new_img = px.toImage()
        ptr = new_img.bits()
        ptr.setsize(new_img.byteCount())
        arr = np.array(ptr, dtype=np.uint8).reshape((h, w, 4))
        final_bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        self.set_image(final_bgr, fit_to_frame=False)
        self.text_editing = False
        self.temp_text = ""

    def open_sticker_window(self):
        if self.image is None:
            return
        sw = StickerWindow(self)
        sw.sticker_applied.connect(self.on_sticker_selected)
        sw.exec_()

    def on_sticker_selected(self, pixmap):
        self.temp_sticker = pixmap
        self.temp_sticker_pos = QPoint(50, 50)
        self.temp_sticker_scale = 1.0
        self.sticker_editing = True
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.image is None:
            return
        painter = QPainter(self)
        painter.translate(self.image_label.pos())

        
        if self.text_editing and self.temp_text:
            painter.setFont(self.temp_font)
            painter.setPen(self.temp_color)
            painter.drawText(self.temp_text_pos, self.temp_text)

        
        if self.sticker_editing and not self.temp_sticker.isNull():
            scaled_width = self.temp_sticker.width() * self.temp_sticker_scale
            scaled_height = self.temp_sticker.height() * self.temp_sticker_scale
            sticker_scaled = self.temp_sticker.scaled(
                scaled_width, scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.temp_sticker_pos.setX(
                max(0, min(self.temp_sticker_pos.x(), self.ui.frame.width() - scaled_width)))
            self.temp_sticker_pos.setY(
                max(0, min(self.temp_sticker_pos.y(), self.ui.frame.height() - scaled_height)))
            painter.drawPixmap(self.temp_sticker_pos, sticker_scaled)
            
            self.scale_handle_rect = QRect(
                self.temp_sticker_pos.x() + sticker_scaled.width() -
                self.scale_handle_size // 2,
                self.temp_sticker_pos.y() + sticker_scaled.height() -
                self.scale_handle_size // 2,
                self.scale_handle_size, self.scale_handle_size
            )
            painter.setPen(Qt.red)
            painter.drawRect(self.scale_handle_rect)

        painter.end()

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
