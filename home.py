# home.py
import sys
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QVBoxLayout, QMessageBox, QDialog
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from Ui_Addition import Ui_MainWindow
from main import MainWindow
import os
from PySide6.QtGui import QIcon

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super(InfoDialog, self).__init__(parent)
        self.setWindowTitle("情報")
        self.setFixedSize(200, 100)
        layout = QVBoxLayout(self)
        self.info_label = QLabel("pypicture\nバージョン: 1.0", self)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

class HomeWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        self.image_label = QLabel(self.ui.frame)
        self.image_label.setGeometry(
            0, 0, self.ui.frame.width(), self.ui.frame.height()
        )
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.history_layout = QVBoxLayout(self.ui.frame)
        self.history_layout.addWidget(self.image_label)

        self.ui.pushButton.clicked.connect(self.create_new_image)
        self.ui.pushButton_2.clicked.connect(self.open_image)

        self.history = []

        self.main_window = MainWindow()

        self.init_menu()
        self.setWindowTitle("PyPicture")  # ウィンドウタイトルを PyPicture に設定
        self.setWindowIcon(QIcon("logo.ico"))

    def init_menu(self):
        menubar = self.menuBar()
        info_menu = menubar.addMenu("情報")

        info_action = QAction("情報", self)
        info_action.triggered.connect(self.show_info_dialog)
        info_menu.addAction(info_action)

    def show_info_dialog(self):
        dialog = InfoDialog(self)
        dialog.exec()

    def create_new_image(self):
        try:
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
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "画像を開く",
                "",
                "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;全てのファイル (*.*)"
            )

            if file_name:
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
