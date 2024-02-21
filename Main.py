import sys
import threading
from pathlib import Path
from time import sleep

import cv2
import yaml
from PIL import ExifTags, Image, ImageOps
import tornado
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox

from mainFrame import Ui_MainWindow as mainWindow
from uitest import Ui_MainWindow as picWindow
from uitest2 import Ui_MainWindow as videoWindow
from uitest3 import Ui_MainWindow as setWindow
from PyQt5 import QtWidgets, QtCore
import torch
import os
from yolov5 import detect

FILE = Path(__file__).resolve()
path = FILE.parents[0]


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ui = mainWindow()
        self.ui.setupUi(self)


class PicWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ui = picWindow()
        self.ui.setupUi(self)
        self.filename_chosen = None
        self.cap = None

    def getFromPicture(self):
        self.ui.pic1.clear()
        self.ui.pic2.clear()
        self.filename_chosen, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                               "All Files(*)")
        width = self.ui.pic1.width()
        height = self.ui.pic1.height()
        try:
            img = QPixmap()
            img.load(self.filename_chosen)
        except:
            return
        img = img.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.pic1.setPixmap(img)
        # self.ui.pic1.setScaledContents(True)  # 饱满缩放

    def detect(self):
        for char in self.filename_chosen:
            if u'\u4e00' <= char <= u'\u9fff':
                msg_box = QMessageBox(QMessageBox.Warning, 'Warning', "请暂时不要使用中文路径")
                msg_box.exec_()
                return
        path1 = detect.run(weights=path / "best.pt", source=self.filename_chosen, show_text=self.ui.label_2)
        width = self.ui.pic2.width()
        height = self.ui.pic2.height()
        img = QPixmap()
        img.load(path1)
        img = img.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.pic2.setPixmap(img)
        return


class VidWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ui = videoWindow()
        self.ui.setupUi(self)
        self.cap = None
        with open(path / 'yolov5/save_path.txt', 'r')as file:
            self.save_path = file.read().strip()
        file1 = open(path / "yolov5/global.txt", 'w')
        file1.write('2')
        file1.close()

    def getFromCamera(self):
        try:  # test for camera
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 0第一个摄像头
            self.cap = None
        except:
            msg_box = QMessageBox(QMessageBox.Warning, 'Warning', "未检测出摄像头！")
            msg_box.exec_()
            return
        with open(path / 'yolov5/save_path.txt', 'r')as file:
            self.save_path = file.read().strip()
            file.close()
        with open(path / "yolov5/global.txt", 'r')as file:
            flag = file.read().strip()
            file.close()
        # while 1:
        #     ret, frame = self.cap.read()
        #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #     width = self.ui.pic1.width()
        #     height = self.ui.pic1.height()
        #     img = QPixmap(QImage(frame, width, height, QImage.Format_RGB888))
        #     img = img.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #     self.ui.pic1.setPixmap(img)
        #     cv2.waitKey(1)
        if flag == '2':
            detect.run(source=0, weights=path / "best.pt", show_camera=self.ui.pic1, show_text=self.ui.label_2, my_save_path=self.save_path)

    def changeFlag(self):
        with open(path / "yolov5/global.txt", 'w')as file1:file1.write('0')

    def ex(self):
        with open(path / "yolov5/global.txt", 'w')as file1:file1.write('2')
        with open(path / "yolov5/save.txt", 'w+')as file1:file1.write('0')

    def getCurrentPic(self):
        with open(path / 'yolov5/save_path.txt', 'r')as file:
            self.save_path = file.read().strip()
            file.close()
        with open(path / "yolov5/save.txt", 'r')as file1:
            temp = file1.read().strip()
            if temp == '0':
                self.ui.pushButton_2.setText("停止截取画面")
            else:
                self.ui.pushButton_2.setText("截取当前画面")
            file1.close()
        with open(path / "yolov5/save.txt", 'w')as file1:
            file1.write(str(1-int(temp)))
            file1.close()


class SetWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ui = setWindow()
        self.ui.setupUi(self)
        self.save_path = None
        self.temp = None
        with open(path / 'yolov5/save_path.txt', 'r')as file:
            self.save_path = file.read().strip()
            self.temp = self.save_path
        self.ui.label_2.setText(self.save_path)

    def choose_dir(self):
        self.temp = QtWidgets.QFileDialog.getExistingDirectory(None, '选取保存路径', 'C:/')
        self.ui.label_2.setText(self.temp)

    def set_dir(self):
        self.save_path = self.temp
        with open(path / 'yolov5/save_path.txt', 'w')as file:
            file.write(self.save_path)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    pw = PicWindow()
    vw = VidWindow()
    sw = SetWindow()
    # 在这里绑定事件实现窗口间的切换
    mw.ui.pushButton.clicked.connect(mw.hide)
    mw.ui.pushButton.clicked.connect(pw.show)
    mw.ui.pushButton_2.clicked.connect(mw.hide)
    mw.ui.pushButton_2.clicked.connect(vw.show)
    mw.ui.pushButton_4.clicked.connect(vw.ex)
    mw.ui.pushButton_3.clicked.connect(mw.hide)
    mw.ui.pushButton_3.clicked.connect(sw.show)

    pw.ui.pushButton_2.clicked.connect(pw.hide)
    pw.ui.pushButton_2.clicked.connect(mw.show)
    vw.ui.pushButton_3.clicked.connect(vw.hide)
    vw.ui.pushButton_3.clicked.connect(mw.show)
    vw.ui.pushButton_3.clicked.connect(vw.changeFlag)
    sw.ui.pushButton.clicked.connect(sw.hide)
    sw.ui.pushButton.clicked.connect(mw.show)
    sw.ui.pushButton_2.clicked.connect(sw.hide)
    sw.ui.pushButton_2.clicked.connect(mw.show)


    mw.show()
    sys.exit(app.exec_())
