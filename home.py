# home.py
import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout, QMessageBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from Ui_Addition import Ui_MainWindow
from main import MainWindow
import os

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
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        try:
            # フレームいっぱいに白画面を作成
            white_image = np.ones(
                (self.ui.frame.height(), self.ui.frame.width(), 3), np.uint8
            ) * 255
            self.main_window.set_image(white_image)
            self.main_window.show()
            self.close()
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", f"新規画像の作成に失敗しました: {str(e)}", QMessageBox.StandardButton.Ok)

    def open_image(self):
        try:
            # Unicode パスの画像を読み込み、フレームに表示
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "画像を開く",
                "",  # 初期ディレクトリを空に設定
                "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;全てのファイル (*.*)"
            )

            if file_name:
                # OpenCV を使用して画像を読み込む
                image = cv2.imdecode(np.fromfile(
                    file_name, dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    QMessageBox.warning(
                        self, "警告", "画像の読み込みに失敗しました", QMessageBox.StandardButton.Ok)
                    return

                self.main_window.set_image(image)
                self.main_window.show()
                self.close()

        except Exception as e:
            QMessageBox.critical(
                self, "エラー", f"画像の読み込み中にエラーが発生しました: {str(e)}", QMessageBox.StandardButton.Ok)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HomeWindow()
    window.show()
    sys.exit(app.exec())
