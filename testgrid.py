from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QDialog,
    QApplication,
    QFileDialog,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QHBoxLayout,
    QGridLayout,
    QGroupBox
)
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.uic import loadUi
from PyQt5 import Qt
import sys
import cv2
from PyQt5.QtCore import QSize, pyqtSignal, pyqtSlot, Qt, QThread, QTime, QTimer,Qt, QMimeData, QByteArray, QDataStream, QIODevice
import numpy as np
import face_recognition
import pickle
import pandas as pd
from datetime import date, datetime
from threading import Event
from face_registeration import register_face



     

class App(QDialog):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 layout - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 100
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        # self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.createGridLayout()
        
        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)
        self.setLayout(windowLayout)
        
        self.show()
    
    def create_frame_widget(self):
        frame_layout = QVBoxLayout()
        frame_widget = QWidget()
        
        label_image = QLabel()
        pixmap = QPixmap(f'face/ball.jpg')
        pixmap = pixmap.scaled(QSize(90,90))
        
        label_image.setPixmap(pixmap)
        label_text = QLabel()
        label_text.setText("ball")
        
        frame_layout.addWidget(label_image)
        frame_layout.addWidget(label_text)
        
        
        frame_widget.setLayout(frame_layout)

        return frame_widget

    def createGridLayout(self):
        self.horizontalGroupBox = QGroupBox("Grid")
        layout = QGridLayout()
        # layout.setColumnStretch(1, 4)
        # layout.setColumnStretch(2, 4)
        
        layout.addWidget(self.create_frame_widget(),0,0)
        layout.addWidget(self.create_frame_widget(),0,1)
        layout.addWidget(self.create_frame_widget(),0,2)
        layout.addWidget(self.create_frame_widget(),1,0)
        layout.addWidget(self.create_frame_widget(),1,1)
        layout.addWidget(self.create_frame_widget(),1,2)
        # layout.addWidget(QPushButton('1'),0,0)
        # layout.addWidget(QPushButton('2'),0,1)
        # layout.addWidget(QPushButton('3'),0,2)
        # layout.addWidget(QPushButton('4'),1,0)
        # layout.addWidget(QPushButton('5'),1,1)
        # layout.addWidget(QPushButton('6'),1,2)
        # layout.addWidget(QPushButton('7'),2,0)
        # layout.addWidget(QPushButton('8'),2,1)
        # layout.addWidget(QPushButton('9'),2,2)
        
        self.horizontalGroupBox.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())