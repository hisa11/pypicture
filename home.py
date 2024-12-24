import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from Ui_Addition import Ui_MainWindow
from main import MainWindow

class HomeWindow(QMainWindow):
    def __init__(self):
        super(HomeWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 画像表示用のラベルをフレームに追加
        self.image_label = QLabel(self.ui.frame)
        self.image_label.setGeometry(
            0, 0, self.ui.frame.width(), self.ui.frame.height()
        )
        self.image_label.setAlignment(Qt.AlignCenter)

        # 編集履歴を表示するためのレイアウト
        self.history_layout = QVBoxLayout(self.ui.frame)
        self.history_layout.addWidget(self.image_label)

        # ボタンのクリックイベントを接続
        self.ui.pushButton.clicked.connect(self.create_new_image)
        self.ui.pushButton_2.clicked.connect(self.open_image)

        # 編集履歴を保存するリスト
        self.history = []

        # MainWindow インスタンスを作成
        self.main_window = MainWindow()

    def create_new_image(self):
        # フレームいっぱいに白画面を作成
        white_image = np.ones(
            (self.ui.frame.height(), self.ui.frame.width(), 3), np.uint8
        ) * 255
        self.main_window.set_image(white_image)
        self.main_window.show()
        self.close()

    def open_image(self):
        # Unicode パスの画像を読み込み、フレームに表示
        file_name, _ = QFileDialog.getOpenFileName(
            self, "画像を開く", "", "画像ファイル (*.png *.jpg *.bmp)"
        )
        if file_name:
            # np.fromfile + cv2.imdecode で日本語パスにも対応
            data = np.fromfile(file_name, np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if image is None or image.size == 0:
                return
            # BGR → RGB 変換
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.main_window.set_image(image)
            self.main_window.show()
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HomeWindow()
    window.show()
    sys.exit(app.exec())
