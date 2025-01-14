from PySide6.QtWidgets import QLabel, QDialog, QMessageBox
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QCursor
from PySide6.QtCore import Qt, QRect, QPoint

class Trimming:
    def __init__(self, image, parent):
        self.image = image.copy()
        self.parent = parent
        self.trim_rect = QRect()

    def trim(self):
        self.parent.cropping = True
        self.parent.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.parent.trim_rect = QRect()
        self.parent.update()

        # イベントループを開始してトリミングを待機
        # ここでは簡略化のため、トリミング後に即座に終了します
        # 実際のアプリケーションではマウスイベントを処理する必要があります
        # 例えば、QEventLoopを使用してトリミングが完了するまで待機する

        # トリミングが完了したかどうかを返します
        return True

    def get_trimmed_image(self):
        if self.trim_rect.isNull():
            QMessageBox.warning(self.parent, "警告", "トリミング範囲が選択されていません。")
            return None

        # フレームと画像のサイズ取得
        self.trim_trimming = Trimming(self.image, self)
        fw = self.parent.ui.frame.width()
        fh = self.parent.ui.frame.height()
        img_h, img_w, _ = self.image.shape

        # 表示中の画像のスケールとオフセットを計算
        final_scale = self.parent.base_scale_factor * self.parent.user_scale_factor
        scaled_w = int(img_w * final_scale)
        scaled_h = int(img_h * final_scale)

        x_display = (fw - scaled_w) // 2 + self.parent.pan_offset_x
        y_display = (fh - scaled_h) // 2 + self.parent.pan_offset_y

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
            QMessageBox.warning(self.parent, "警告", "選択範囲が小さすぎます。")
            self.parent.update_image()
            return None

        # トリミング実行
        roi = self.image[y1:y2, x1:x2].copy()

        # トリミング後の画像を元の位置に戻すためのオフセット調整
        self.parent.pan_offset_x += int((self.trim_rect.left() - x_display))
        self.parent.pan_offset_y += int((self.trim_rect.top() - y_display))

        return roi
