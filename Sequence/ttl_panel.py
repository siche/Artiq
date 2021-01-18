
import os
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
# from PyQt5.QtWidgets import QDoubleSpinBox, QApplication, QHBoxLayout, QGroupBox, QWidget, QPushButton, QGridLayout, QLabel
import socket
import sys
from ctypes import *

myfont = QFont()
myfont.setBold(True)

class LVSpinBox(QDoubleSpinBox):
    '''This class is a reimplemented double spinbox with the same function as LabView number control'''
    stepChanged = pyqtSignal()

    def stepBy(self, step):
        value = self.value()
        point = str(self.text()).find('.')
        if point < 0:
            point = len(str(self.text()))
        digit = point - self.lineEdit().cursorPosition()
        if digit < 0:
            digit += 1
        self.setValue(value + step*(10**digit))
        if self.value() != value:
            self.stepChanged.emit()

    def onValueChanged(self, func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)

class AD5791:
    """This class is designed to control AD5791, and I have set the LDAC at the Low level which enable Synchronous DAC Update 
 at the rising edge of SYNC."""
    def __init__(self, ser="BSPT002029", dll="usb2uis.dll"):
        self.VREF = 10.0
        self.serial_num = ser
        self.dll = cdll.LoadLibrary(dll)
        # Close the connections if already exist
        self.dll.USBIO_CloseDeviceByNumber(ser)
        self.device_num = self.dll.USBIO_OpenDeviceByNumber(ser)
        if self.device_num == 0xFF:
            print("No USB2UIS can be connected!")
            exit()
        self.SPI_Init()
        self.device_start()
        
    def SPI_Init(self, frequency=8, mode=1, timeout_read=100, timeout_write=100):
        """SPI settings, frequency upto 8 selections, representing 200kHz 400kHz, 600kHz, 800kHz, 1MHz, 2MHz, 4MHz, 6MHz and 12MHz. Mode is specified to the clock signal, and the timeout is used to specify the timeout of read and write, occupying 16-bit data respectively"""
        self.dll.USBIO_SPISetConfig(self.device_num, (mode<<4)+frequency, (timeout_write<<16)+timeout_read)

    def data(self, Vout):
        return int((Vout+self.VREF)*(2**20-1)/2/self.VREF)
    
    def device_start(self):
        """Set the control register to enable the dac into a normal operation mode and offset code style"""
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x200012).to_bytes(3, byteorder="big"), 3)
    def set_voltage(self, Vout):
        """The Vout set to the DAC should exceed \pm 10V"""
        if abs(Vout)>10.0000000001:
            print("Voltage over range!")
        else:
            self.dll.USBIO_SPIWrite(self.device_num, None, 0, ((0x01<<20) + self.data(Vout)).to_bytes(3, byteorder="big"), 3)
    def read_voltage(self):
        out = b'\x00'*3
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x900000).to_bytes(3, byteorder="big"), 3)
        self.dll.USBIO_SPIRead(self.device_num, None, 0, out, 3)
        data = int.from_bytes(out, byteorder="big")
        data = data&0x0FFFFF
        return data*2*self.VREF/(2**20 - 1) - self.VREF

    def LDAC(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x400001).to_bytes(3, byteorder="big"), 3)
    def clear(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x400002).to_bytes(3, byteorder="big"), 3)
    def reset(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x400004).to_bytes(3, byteorder="big"), 3)
    def disable_output(self):
        self.dll.USBIO_SPIWrite(self.device_num, None, 0, (0x20001E).to_bytes(3, byteorder="big"), 3)
    def __del__(self):
        self.dll.USBIO_CloseDeviceByNumber(self.serial_num)

class AD5791Ctrl(QGroupBox):
    def __init__(self, ser="BSPT002029", dll="usb2uis.dll"):
        super().__init__()
        self.device = AD5791(ser, dll)
        self.value = LVSpinBox()
        self.value.setDecimals(3)
        self.value.setValue(self.device.read_voltage())
        self.switch = QPushButton("ON")
        self.switch.setCheckable(True)
        self.switch.setChecked(True)
        self.switch.setStyleSheet("background-color: green")
        self.switch.setFont(myfont)
        self.reset = QPushButton("Reset")
        self.reset.setFont(myfont)
        self.level = QPushButton("High")
        self.level.setCheckable(True)
        self.level.setChecked(True)
        self.level.setFont(myfont)
        self.level.setStyleSheet("background-color: red")
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Vref"), 0)
        layout.addWidget(self.value, 1)
        layout.addWidget(self.level, 1)
        layout.addWidget(self.switch, 1)
        layout.addWidget(self.reset, 1)
        self.setLayout(layout)
        self.set_connect()
        self.level.setChecked(False)
        

    def setRange(self, low=1.4, upper=5.0):
        self.value.setRange(low, upper)

    def set_connect(self):
        self.value.valueChanged.connect(self.set_voltage)
        self.switch.toggled.connect(self.set_switch)
        self.reset.clicked.connect(self.resetAll)
        self.level.toggled.connect(self.changeLevel)
    def set_voltage(self):
        self.device.set_voltage(self.value.value())
    def set_switch(self):
        if self.switch.isChecked():
            self.device.device_start()
            self.level.setChecked(False)
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.device.disable_output()
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")
    def resetAll(self):
        self.device.reset()
        self.switch.setChecked(False)
        self.value.setValue(self.device.read_voltage())
    def changeLevel(self):
        if self.level.isChecked():
            self.value.setValue(3.5)
            self.level.setStyleSheet("background-color: green")
            self.level.setText("High")
        else:
            self.value.setValue(1.4)
            self.level.setStyleSheet("background-color: red")
            self.level.setText("Low")
    def setHighLevel(self, state):
        if state:
            self.level.setChecked(True)
        else:
            self.level.setChecked(False)

class ttl_panel(QWidget):
    def __init__(self, parent=None):
        super(ttl_panel, self).__init__(parent)
        self.ip = '192.168.1.16'
        self.port = 6666
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        self.ons = [False, False, False]
        self.initUi()
        print(self.sock.recv(1024).decode('utf-8'))

    def initUi(self):
        btn0 = QPushButton('off')
        btn0.setStyleSheet('background-color:red;')
        btn0.clicked.connect(lambda: self.on_off(0))
        label0 = QLabel('370 zero shutter')

        btn1 = QPushButton('off')
        btn1.setStyleSheet('background-color:red;')
        btn1.clicked.connect(lambda: self.on_off(1))
        label1 = QLabel('Flip mirror')

        btn2 = QPushButton('off')
        btn2.setStyleSheet('background-color:red;')
        btn2.clicked.connect(lambda: self.on_off(2))
        label2 = QLabel('399 Shutter')

        layout = QGridLayout()
        layout.addWidget(label0, 1, 0)
        layout.addWidget(btn0, 1, 1)

        layout.addWidget(label1, 2, 0)
        layout.addWidget(btn1, 2, 1)

        layout.addWidget(label2, 3, 0)
        layout.addWidget(btn2, 3, 1)

        vref = AD5791Ctrl()
        vref.setRange(1.0, 4.0)
        vref.setTitle("RF Reference")
        layout.addWidget(vref,4,0,1,2)
        
        self.setLayout(layout)
        self.btns = [btn0, btn1, btn2]

        # self.btns =[self.btn0,self.btn1,self.btn2]

    def on_off(self, num=0):
        self.ons[num] = not self.ons[num]
        btn_temp = self.btns[num]
        # cmd = 'self.btn'+str(num)
        #self.btn0 = self.btn0
        # self.btn0 = self.btns[num]
        if not self.ons[num]:
            btn_temp.setStyleSheet('background-color:red;')
            btn_temp.setText('off')

            code = str(num) + ' off'

            self.sock.send(code.encode('utf-8'))
            print(self.sock.recv(1024).decode('utf-8'))
            # print('RF is on')
        else:
            btn_temp.setStyleSheet('background-color:green;')
            btn_temp.setText('on')

            code = str(num) + ' on'

            self.sock.send(code.encode('utf-8'))
            print(self.sock.recv(1024).decode('utf-8'))
            # print('RF is off')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = ttl_panel()
    ex.show()
    sys.exit(app.exec_())
