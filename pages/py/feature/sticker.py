import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QGuiApplication

class StickerWindow(QDialog):
    sticker_applied = Signal(QPixmap)

    def __init__(self, parent=None):
        super(StickerWindow, self).__init__(parent)
        self.setWindowTitle("ステッカー選択")
        self.setFixedSize(300, 120)

        self.main_layout = QVBoxLayout(self)

        # ステッカー画像プレビュー
        self.preview_label = QLabel("プレビュー: なし")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.selected_pixmap = QPixmap()

        # ファイルから選択ボタン
        self.file_button = QPushButton("ファイルから選択")
        self.file_button.clicked.connect(self.load_from_file)

        # クリップボードから取得ボタン
        self.clipboard_button = QPushButton("クリップボードから取得")
        self.clipboard_button.clicked.connect(self.load_from_clipboard)

        # OKボタン
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.apply_sticker)

        # レイアウト構成
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.file_button)
        btn_layout.addWidget(self.clipboard_button)

        self.main_layout.addWidget(self.preview_label)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.ok_button)

    def load_from_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "ステッカー画像を選択", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_name:
            pix = QPixmap(file_name)
            if not pix.isNull():
                self.selected_pixmap = pix
                self.preview_label.setText("")
                self.preview_label.setPixmap(
                    self.selected_pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )

    def load_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            pix = clipboard.image()
            qpixmap = QPixmap.fromImage(pix)
            if not qpixmap.isNull():
                self.selected_pixmap = qpixmap
                self.preview_label.setText("")
                self.preview_label.setPixmap(
                    self.selected_pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )
        else:
            self.preview_label.setText("クリップボードに画像がありません")

    def apply_sticker(self):
        if not self.selected_pixmap.isNull():
            self.sticker_applied.emit(self.selected_pixmap)
        self.accept()
