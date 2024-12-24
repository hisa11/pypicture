import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from picture import Ui_MainWindow  # 変換されたファイルをインポート

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # QLabel を作成してフレームに追加
        self.label = QLabel(self.ui.frame)  # フレーム内に配置
        self.label.setGeometry(0, 0, self.ui.frame.width(),
                               self.ui.frame.height())  # フレーム全体に配置
        self.label.setScaledContents(True)  # 画像を自動でサイズ調整
        self.label.setAlignment(Qt.AlignCenter)

        # 白い画像を QLabel に設定
        pixmap = QPixmap("white_image.png")  # 画像ファイルを読み込む
        if not pixmap.isNull():
            self.label.setPixmap(pixmap)
        else:
            print("画像が見つかりません")
    def set_image(self, image):
        """フレーム内に画像を設定"""
        qimage = QImage(
            image.data, image.shape[1], image.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        # 画像の縦横比を維持しながら最大化
        label_width = self.ui.frame.width()
        label_height = self.ui.frame.height()

        # 画像を拡大する割合を計算
        scale_factor = min(label_width / pixmap.width(),
                           label_height / pixmap.height())

        # 画像を拡大
        new_width = int(pixmap.width() * scale_factor)
        new_height = int(pixmap.height() * scale_factor)
        pixmap = pixmap.scaled(new_width, new_height,
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.label.setPixmap(pixmap)
        self.label.setGeometry(
            (label_width - new_width) // 2, (label_height - new_height) // 2, new_width, new_height)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

