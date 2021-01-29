import os
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
# from PyQt5.QtWidgets import QDoubleSpinBox, QApplication, QHBoxLayout, QGroupBox, QWidget, QPushButton, QGridLayout, QLabel

import sys, signal
from CurrentWebClient import current_web

myfont = QFont('Arial', 16, 24)
myfont.setBold(True)

class Current_Ctrl(QWidget):

    def __init__(self, parent = None):
        super(Current_Ctrl, self).__init__(parent)
        self.curr = current_web()
        self.initUi()
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    
    def initUi(self):

        label0 = QLabel('Current')
        label0.setFont(myfont)

        btn1 = QDoubleSpinBox()
        btn1.setRange(0.0,3.1)
        btn1.setDecimals(1)
        btn1.setValue(3.1)
        btn1.setSingleStep(0.1)
        btn1.setFont(myfont)

        btn2 = QPushButton('OFF')
        btn2.setCheckable(True)
        btn2.setChecked(False)
        btn2.setStyleSheet('background-color:red')
        btn2.toggled.connect(self.on_off)
        btn2.setFont(myfont)

        btn3 = QPushButton('set')
        # btn3.setCheckable(True)
        # btn3.setChecked(False)
        btn3.setStyleSheet('background-color:green')
        btn3.toggled.connect(self.set_value)
        btn3.setFont(myfont)

        layout = QGridLayout()
        layout.addWidget(label0,0,0)
        layout.addWidget(btn1,0,1)
        layout.addWidget(btn3,0,2)
        layout.addWidget(btn2,0,3)
        
        self.btn1 = btn1
        self.btn2 = btn2
        self.setLayout(layout)
        self.show()

    def on_off(self):
        if self.btn2.isChecked():
            self.btn2.setText('ON')
            self.btn2.setStyleSheet('background-color:green')
            current_value = self.btn1.value()
            self.curr.set_up(curr=current_value, vol=2)
            self.curr.on()

        else:
            self.btn2.setText('OFF')
            self.btn2.setStyleSheet('background-color:red')
            self.curr.off()

    def set_value(self):
        current_value = self.btn1.value()
        self.curr.set_up(curr=current_value, vol=2)
        # self.curr.off()
        
    def exit(self,signum, frame):
        self.curr.off()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ex = Current_Ctrl()
    ex.show()
    sys.exit(app.exec_())