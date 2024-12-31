import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QDialog
from PySide6.QtGui import QPixmap, QImage, QWheelEvent, QPainter, QPen, QCursor
from PySide6.QtCore import Qt, QRect
from picture import Ui_MainWindow
from revolution import RevolutionWindow
from brightness import BrightnessWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # フレーム内に画像を貼り付けるラベル
        self.image_label = QLabel(self.ui.frame)
        self.image_label.setGeometry(
            0, 0, self.ui.frame.width(), self.ui.frame.height())
        self.image_label.setAlignment(Qt.AlignCenter)

        # レイアウトをフレームに設定
        self.history_layout = QVBoxLayout(self.ui.frame)
        self.history_layout.addWidget(self.image_label)

        # 画像関連
        self.image = None
        self.display_image_cache = None

        # ズーム関連
        self.user_scale_factor = 1.0  # ユーザー操作による相対倍率
        self.base_scale_factor = 1.0  # 画像を“ちょうど”or“等倍”で表示するときの基準倍率

        # トリミング関連
        self.cropping = False
        self.rect = QRect()

        # UIの各ボタンに処理を割り当て
        self.ui.trimming.clicked.connect(self.start_trimming)
        self.ui.revolution.clicked.connect(self.open_revolution_window)
        self.ui.brightness.clicked.connect(self.open_brightness_window)

    def set_image(self, image, fit_to_frame=True):
        """画像を設定し、必要に応じてフレームに fitting or 等倍表示を基準とする。"""
        self.image = np.ascontiguousarray(image)
        self.display_image_cache = None  # キャッシュリセット
        # fit_to_frame=True の場合は「フレームより大きいなら縮小して100%」、小さいなら等倍が100%になるよう base_scale_factor を求める
        if fit_to_frame:
            self.calc_base_scale_factor()
            # ここで拡大率をリセット（100%相当）
            self.user_scale_factor = 1.0
        self.update_image()

    def calc_base_scale_factor(self):
        """画像がフレームより大きいときは縮小してピッタリに合わせる。それ以外は等倍を基準(100%)にする。"""
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

        # 画像がフレームより大きい時のみ縮小基準にする
        if scale_fit < 1.0:
            # フレームに合わせて縮小する倍率を「100%」とする
            self.base_scale_factor = scale_fit
        else:
            # 画像がフレームより小さければ等倍を「100%」にする
            self.base_scale_factor = 1.0

    def update_image(self):
        """base_scale_factor × user_scale_factor で画像を拡大／縮小して表示。"""
        if self.image is None:
            return

        # まだキャッシュ化されていなければ作成
        if self.display_image_cache is None:
            h, w, _ = self.image.shape
            qimg = QImage(self.image.data, w, h, w * 3,
                          QImage.Format_RGB888).rgbSwapped()
            self.display_image_cache = QPixmap.fromImage(qimg)

        final_scale = self.base_scale_factor * self.user_scale_factor

        # 上限は5倍まで
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
        self.image_label.setPixmap(scaled_pixmap)

        # センタリング
        fw = self.ui.frame.width()
        fh = self.ui.frame.height()
        self.image_label.setGeometry(
            (fw - new_width) // 2,
            (fh - new_height) // 2,
            new_width,
            new_height
        )

    def wheelEvent(self, event: QWheelEvent):
        """マウスホイールによる拡大・縮小"""
        if self.image is None:
            return
        if event.angleDelta().y() > 0:
            # 拡大
            self.user_scale_factor *= 1.1
        else:
            # 縮小
            self.user_scale_factor /= 1.1
        self.update_image()

    def start_trimming(self):
        if self.image is None:
            return
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.cropping = True
        # トリミング中に100%に戻すなら下記のようにする:
        # self.user_scale_factor = 1.0
        # self.update_image()

    def mousePressEvent(self, event):
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            self.rect.setTopLeft(self.image_label.mapFromParent(event.pos()))
            self.rect.setBottomRight(
                self.image_label.mapFromParent(event.pos()))

    def mouseMoveEvent(self, event):
        if self.cropping:
            self.rect.setBottomRight(
                self.image_label.mapFromParent(event.pos()))
            self.update()

    def mouseReleaseEvent(self, event):
        if self.cropping and event.button() == Qt.MouseButton.LeftButton:
            self.rect.setBottomRight(
                self.image_label.mapFromParent(event.pos()))
            self.cropping = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            # 必要ならここでトリミング処理
            # self.crop_image()
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
        rev = RevolutionWindow(self.image, self)
        rev.angle_changed.connect(self.update_rotated_image)
        if rev.exec_() == QDialog.Accepted:
            self.set_image(rev.get_rotated_image(), fit_to_frame=False)

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
        """明るさ調整のリアルタイム反映"""
        bw = self.sender()
        if bw:
            adjusted = bw.get_adjusted_image()
            # 画像だけ差し替え
            self.image = adjusted
            self.display_image_cache = None
            self.update_image()

    def update_rotated_image(self, angle):
        """回転操作のリアルタイム反映"""
        rw = self.sender()
        if rw:
            rotated = rw.get_rotated_image()
            # 画像だけ差し替え
            self.image = rotated
            self.display_image_cache = None
            self.update_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
