import sys
import numpy as np
import cv2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QDialog, QFileDialog,
    QMessageBox, QWidget
)
from PySide6.QtGui import (
    QPixmap, QImage, QWheelEvent, QPainter, QCursor,
    QFont, QColor, QFontMetrics, QPen
)
from PySide6.QtCore import Qt, QRect, QPoint, QSize, QTimer


from pages.ui.picture import Ui_MainWindow
from pages.py.feature.revolution import RevolutionWindow
from pages.py.feature.brightness import BrightnessWindow
from pages.py.feature.contrast import ContrastWindow
from pages.py.feature.shadow import ShadowWindow
from pages.py.feature.chroma import ChromaWindow
from pages.py.feature.color import ColorWindow
from pages.py.feature.text import TextWindow
from pages.py.feature.sticker import StickerWindow
from pages.py.feature.retouch import RetouchWindow
from pages.py.feature.save import SaveWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setMouseTracking(True)
        self.ui.frame.setMouseTracking(True)

        self.image_label = QLabel(self.ui.frame)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # レイアウト削除（手動セットGeometryを活かすため）
        # self.history_layout = QVBoxLayout(self.ui.frame)
        # self.history_layout.addWidget(self.image_label)

        self.setFixedSize(self.size())

        self.image = None
        self.display_image_cache = None

        self.user_scale_factor = 1.0
        self.base_scale_factor = 1.0

        # パン用
        self.is_panning = False
        self.last_pan_pos = QPoint()
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.pan_start_pos = QPoint()
        self.pan_active = False

        # トリミング用
        self.cropping = False
        self.trim_rect = QRect()

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

        # パン用タイマー
        self.pan_timer = QTimer(self)
        self.pan_timer.setSingleShot(True)
        self.pan_timer.timeout.connect(self.start_panning)
        self.pan_timer_interval = 100  # ミリ秒

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

        self.setWindowTitle("PyPicture")  # ウィンドウタイトルを PyPicture に設定
        self.setWindowIcon(QPixmap("logo.ico"))  # アイコンを設定

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
                      QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimg)
        frame_w = self.ui.frame.width()
        frame_h = self.ui.frame.height()
        scale_fit = min(frame_w / pixmap.width(), frame_h / pixmap.height())
        self.base_scale_factor = scale_fit if scale_fit < 1.0 else 1.

        final_scale = self.base_scale_factor * self.user_scale_factor
        # 最大5倍、最小0.5倍に制限
        if final_scale > 5.0:
            self.user_scale_factor = 5.0 / self.base_scale_factor
        if final_scale < 0.1:
            self.user_scale_factor = 0.1 / self.base_scale_factor

        h_img, w_img, _ = self.image.shape
        scaled_w = int(w_img * final_scale)
        scaled_h = int(h_img * final_scale)

        fw = self.ui.frame.width()
        fh = self.ui.frame.height()

        x_display = (fw - scaled_w) // 2 + self.pan_offset_x
        y_display = (fh - scaled_h) // 2 + self.pan_offset_y
        display_rect = QRect(x_display, y_display, scaled_w, scaled_h)
        frame_rect = QRect(0, 0, fw, fh)

        clipped = display_rect.intersected(frame_rect)
        if clipped.isEmpty():
            self.image_label.clear()
            return

        clipped_x = clipped.x() - x_display
        clipped_y = clipped.y() - y_display
        ratio = 1.0 / final_scale

        src_x = int(clipped_x * ratio)
        src_y = int(clipped_y * ratio)
        src_w = int(clipped.width() * ratio)
        src_h = int(clipped.height() * ratio)

        src_roi = self.image[src_y:src_y + src_h, src_x:src_x + src_w].copy()
        qimg_roi = QImage(src_roi.data, src_roi.shape[1], src_roi.shape[0],
                          src_roi.shape[1] * 3, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap_roi = QPixmap.fromImage(qimg_roi).scaled(
            clipped.width(), clipped.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(pixmap_roi)
        self.image_label.setGeometry(clipped)
        self.update()
        # print(f"Partial update: {clipped}, src=({src_x},{src_y},{src_w},{src_h})")

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
        if extension in ['jpg', 'jpeg']:
            cv2.imwrite(file_path, self.image, [
                        int(cv2.IMWRITE_JPEG_QUALITY), quality])
        else:
            cv2.imwrite(file_path, self.image)
        QMessageBox.information(self, "完了", "画像が保存されました。")

    def mousePressEvent(self, event):
        if self.image is None:
            return

        # トリミング中は視点移動を無効化
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            self.trim_start_pos = event.pos()
            self.trim_rect = QRect(event.pos(), QSize())
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.pan_start_pos = event.pos()
            self.pan_timer.start(self.pan_timer_interval)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def start_panning(self):
        self.is_panning = True
        self.last_pan_pos = self.pan_start_pos
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.pan_timer.isActive():
                self.pan_timer.stop()
            if self.is_panning:
                self.is_panning = False
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        elif event.button() == Qt.MouseButton.MiddleButton:
            if self.is_panning:
                self.is_panning = False
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            self.trim_end_pos = event.pos()
            self.cropping = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.perform_trimming()

    def wheelEvent(self, event: QWheelEvent):
        if self.image is None:
            return
        old_scale = self.user_scale_factor
        if event.angleDelta().y() > 0:
            self.user_scale_factor *= 1.1
        else:
            self.user_scale_factor /= 1.1
        ratio = self.user_scale_factor / old_scale
        self.pan_offset_x = int(self.pan_offset_x * ratio)
        self.pan_offset_y = int(self.pan_offset_y * ratio)
        self.update_image()

    def start_trimming(self):
        if self.image is None:
            QMessageBox.warning(self, "警告", "画像がありません。")
            return
        self.cropping = True
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.trim_rect = QRect()
        self.update()

    def perform_trimming(self):
        if self.trim_rect.isNull():
            return

        # 画像とウィンドウのサイズを取得
        fw = self.ui.frame.width()
        fh = self.ui.frame.height()
        img_h, img_w, _ = self.image.shape

        # 表示中の画像のスケールとオフセットを計算
        final_scale = self.base_scale_factor * self.user_scale_factor
        scaled_w = int(img_w * final_scale)
        scaled_h = int(img_h * final_scale)

        x_display = (fw - scaled_w) // 2 + self.pan_offset_x
        y_display = (fh - scaled_h) // 2 + self.pan_offset_y

        # トリミング矩形を画像座標に変換
        x1 = (self.trim_rect.left() - x_display) / final_scale
        y1 = (self.trim_rect.top() - y_display) / final_scale
        x2 = (self.trim_rect.right() - x_display) / final_scale
        y2 = (self.trim_rect.bottom() - y_display) / final_scale

        # 座標を整数にし、画像範囲内に制限
        x1, x2 = sorted([max(0, min(int(x1), img_w - 1)),
                        max(0, min(int(x2), img_w - 1))])
        y1, y2 = sorted([max(0, min(int(y1), img_h - 1)),
                        max(0, min(int(y2), img_h - 1))])

        if x2 - x1 < 10 or y2 - y1 < 10:
            QMessageBox.warning(self, "警告", "選択範囲が小さすぎます。")
            self.update_image()
            return

        # トリミング実行
        roi = self.image[y1:y2, x1:x2].copy()
        self.set_image(roi, fit_to_frame=True)

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
                      QImage.Format.Format_RGB888).rgbSwapped()
        pixmap_preview = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap_preview)
        self.image_label.setGeometry(
            (self.ui.frame.width() - pixmap_preview.width()) // 2 + self.pan_offset_x,
            (self.ui.frame.height() - pixmap_preview.height()) // 2 + self.pan_offset_y,
            pixmap_preview.width(),
            pixmap_preview.height()
        )
        self.update()

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
        cv_img = QImage(img_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        px = QPixmap.fromImage(cv_img)

        painter = QPainter(px)
        painter.setFont(self.temp_font)
        painter.setPen(self.temp_color)
        painter.drawText(self.temp_text_pos, self.temp_text)
        painter.end()

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
        self.sticker_editing = True
        self.temp_sticker = pixmap
        # フレーム中央へ配置
        frame_width = self.ui.frame.width()
        frame_height = self.ui.frame.height()
        sticker_width = self.temp_sticker.width()
        sticker_height = self.temp_sticker.height()
        self.temp_sticker_pos = QPoint(
            (frame_width - sticker_width) // 2,
            (frame_height - sticker_height) // 2
        )
        self.update()

    def update_image(self):
        if self.image is None:
            self.image_label.clear()
            return

        final_scale = self.base_scale_factor * self.user_scale_factor
        # 最大5倍、最小0.5倍に制限
        if final_scale > 5.0:
            final_scale = 5.0
            self.user_scale_factor = final_scale / self.base_scale_factor
        if final_scale < 0.5:
            final_scale = 0.5
            self.user_scale_factor = final_scale / self.base_scale_factor

        h_img, w_img, _ = self.image.shape
        scaled_w = int(w_img * final_scale)
        scaled_h = int(h_img * final_scale)

        fw = self.ui.frame.width()
        fh = self.ui.frame.height()

        x_display = (fw - scaled_w) // 2 + self.pan_offset_x
        y_display = (fh - scaled_h) // 2 + self.pan_offset_y
        display_rect = QRect(x_display, y_display, scaled_w, scaled_h)
        frame_rect = QRect(0, 0, fw, fh)

        clipped = display_rect.intersected(frame_rect)
        if clipped.isEmpty():
            self.image_label.clear()
            return

        clipped_x = clipped.x() - x_display
        clipped_y = clipped.y() - y_display
        ratio = 1.0 / final_scale

        src_x = int(clipped_x * ratio)
        src_y = int(clipped_y * ratio)
        src_w = int(clipped.width() * ratio)
        src_h = int(clipped.height() * ratio)

        src_roi = self.image[src_y:src_y + src_h, src_x:src_x + src_w].copy()
        qimg_roi = QImage(src_roi.data, src_roi.shape[1], src_roi.shape[0],
                          src_roi.shape[1] * 3, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap_roi = QPixmap.fromImage(qimg_roi).scaled(
            clipped.width(), clipped.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(pixmap_roi)
        self.image_label.setGeometry(clipped)
        self.update()

    def mouseMoveEvent(self, event):
        if self.cropping:
            current_pos = event.pos()
            self.trim_rect.setBottomRight(current_pos)
            self.update()
            return

        if self.is_panning:
            delta = event.pos() - self.last_pan_pos
            self.pan_offset_x += delta.x()
            self.pan_offset_y += delta.y()
            self.last_pan_pos = event.pos()
            self.update_image()

    def paintEvent(self, event):
        super().paintEvent(event)
        # トリミング矩形の描画
        if self.cropping and not self.trim_rect.isNull():
            painter = QPainter(self)
            painter.setPen(QPen(Qt.GlobalColor.green, 2))
            painter.drawRect(self.trim_rect)
            painter.end()

        if self.image is None:
            return

        painter = QPainter(self)
        painter.translate(self.image_label.pos())

        # テキスト描画
        if getattr(self, "text_editing", False) and getattr(self, "temp_text", ""):
            painter.setFont(self.temp_font)
            painter.setPen(self.temp_color)
            painter.drawText(self.temp_text_pos, self.temp_text)

        # ステッカー描画
        if getattr(self, "sticker_editing", False) and not self.temp_sticker.isNull():
            scaled_width = self.temp_sticker.width() * self.temp_sticker_scale
            scaled_height = self.temp_sticker.height() * self.temp_sticker_scale
            sticker_scaled = self.temp_sticker.scaled(
                scaled_width, scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.temp_sticker_pos.setX(
                max(0, min(self.temp_sticker_pos.x(),
                    self.ui.frame.width() - scaled_width))
            )
            self.temp_sticker_pos.setY(
                max(0, min(self.temp_sticker_pos.y(),
                    self.ui.frame.height() - scaled_height))
            )
            painter.drawPixmap(self.temp_sticker_pos, sticker_scaled)

        painter.end()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
