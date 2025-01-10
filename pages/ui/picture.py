# picture.py
# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1011, 586)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(30, 30, 951, 491))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.trimming = QPushButton(self.centralwidget)
        self.trimming.setObjectName(u"trimming")
        self.trimming.setGeometry(QRect(30, 0, 61, 24))
        self.revolution = QPushButton(self.centralwidget)
        self.revolution.setObjectName(u"revolution")
        self.revolution.setGeometry(QRect(90, 0, 51, 24))
        self.brightness = QPushButton(self.centralwidget)
        self.brightness.setObjectName(u"brightness")
        self.brightness.setGeometry(QRect(140, 0, 41, 24))
        self.contrast = QPushButton(self.centralwidget)
        self.contrast.setObjectName(u"contrast")
        self.contrast.setGeometry(QRect(180, 0, 61, 24))
        self.text = QPushButton(self.centralwidget)
        self.text.setObjectName(u"text")
        self.text.setGeometry(QRect(380, 0, 51, 24))
        self.sticker = QPushButton(self.centralwidget)
        self.sticker.setObjectName(u"sticker")
        self.sticker.setGeometry(QRect(430, 0, 61, 24))
        self.color = QPushButton(self.centralwidget)
        self.color.setObjectName(u"color")
        self.color.setGeometry(QRect(330, 0, 51, 24))
        self.shadow = QPushButton(self.centralwidget)
        self.shadow.setObjectName(u"shadow")
        self.shadow.setGeometry(QRect(240, 0, 51, 24))
        self.chroma = QPushButton(self.centralwidget)
        self.chroma.setObjectName(u"chroma")
        self.chroma.setGeometry(QRect(290, 0, 41, 24))
        self.retouch = QPushButton(self.centralwidget)
        self.retouch.setObjectName(u"retouch")
        self.retouch.setGeometry(QRect(490, 0, 51, 24))
        self.save = QPushButton(self.centralwidget)
        self.save.setObjectName(u"save")
        self.save.setGeometry(QRect(890, 0, 91, 24))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1011, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.trimming.setText(QCoreApplication.translate("MainWindow", u"\u30c8\u30ea\u30df\u30f3\u30b0", None))
        self.revolution.setText(QCoreApplication.translate("MainWindow", u"\u56de\u8ee2", None))
        self.brightness.setText(QCoreApplication.translate("MainWindow", u"\u660e\u308b\u3055", None))
        self.contrast.setText(QCoreApplication.translate("MainWindow", u"\u30b3\u30f3\u30c8\u30e9\u30b9\u30c8", None))
        self.text.setText(QCoreApplication.translate("MainWindow", u"\u30c6\u30ad\u30b9\u30c8", None))
        self.sticker.setText(QCoreApplication.translate("MainWindow", u"\u30b9\u30c6\u30c3\u30ab\u30fc", None))
        self.color.setText(QCoreApplication.translate("MainWindow", u"\u8272\u8abf\u6574", None))
        self.shadow.setText(QCoreApplication.translate("MainWindow", u"\u30b7\u30e3\u30c9\u30a6", None))
        self.chroma.setText(QCoreApplication.translate("MainWindow", u"\u5f69\u5ea6", None))
        self.retouch.setText(QCoreApplication.translate("MainWindow", u"\u30ec\u30bf\u30c3\u30c1", None))
        self.save.setText(QCoreApplication.translate("MainWindow", u"\u753b\u50cf\u3092\u65b0\u898f\u4fdd\u5b58", None))
    # retranslateUi

