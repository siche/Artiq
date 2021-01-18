
import os
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
# from PyQt5.QtWidgets import QDoubleSpinBox, QApplication, QHBoxLayout, QGroupBox, QWidget, QPushButton, QGridLayout, QLabel

import sys
from ttl_client import shutter

class ttl_panel(QWidget):
    def __init__(self, parent=None):
        super(ttl_panel, self).__init__(parent)
        self.shutter = shutter(com=1)
        self.initUi()

    def initUi(self):
        btn0 = QPushButton('CCD')
        btn0.setStyleSheet('background-color:green;')
        btn0.clicked.connect(lambda: self.on_off(0))

        btn1 = QPushButton('PMT')
        btn1.setStyleSheet('background-color:blue;')
        btn1.clicked.connect(lambda: self.on_off(1))

        layout = QGridLayout()
        layout.addWidget(btn0, 1, 0)
        layout.addWidget(btn1, 1, 1)

        self.setLayout(layout)

        # self.btns =[self.btn0,self.btn1,self.btn2]

    def on_off(self,num):
    
        if num==0:
            self.shutter.on()
        if num==1:
            self.shutter.off()
       
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = ttl_panel()
    ex.show()
    sys.exit(app.exec_())
