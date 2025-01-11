import cv2
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QSlider,
    QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal

class SaveWindow(QDialog):
    save_completed = Signal(str, int)

    def __init__(self, parent=None):
        super(SaveWindow, self).__init__(parent)
        self.setWindowTitle("画像を保存")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        # 拡張子選択
        self.extension_label = QLabel("拡張子:")
        layout.addWidget(self.extension_label)

        self.extension_combo = QComboBox()
        self.extension_combo.addItems([
            ".bmp", ".dib", ".pbm", ".pgm", ".ppm", ".pnm",
            ".pxm", ".pfm", ".sr", ".png", ".jpg", ".jpeg",
            ".webp", ".avif", ".tiff"
        ])
        layout.addWidget(self.extension_combo)

        # 画質選択
        self.quality_label = QLabel("画質:")
        layout.addWidget(self.quality_label)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(90)
        layout.addWidget(self.quality_slider)

        # 保存ボタン
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_image)
        layout.addWidget(self.save_button)

    def save_image(self):
        options = QFileDialog.Options()
        selected_extension = self.extension_combo.currentText()
        filter_str = f"{selected_extension.upper()} Files (*{selected_extension});;All Files (*)"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "画像を保存", "", filter_str, options=options
        )
        if file_path:
            extension = self.extension_combo.currentText()
            quality = self.quality_slider.value()
            self.save_completed.emit(file_path + extension, quality)
            self.accept()
        else:
            QMessageBox.warning(self, "警告", "ファイル名を入力してください。")
