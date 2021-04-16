import sys

from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication
from PyQt5.QtWidgets import QPushButton, QLabel, QDoubleSpinBox, QLineEdit, QTextEdit, QComboBox, QStatusBar, QFrame
from PyQt5.QtWidgets import QLayout, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QFont, QPalette

class MainWindow_UI(QMainWindow):
    def __init__(self):
        super(MainWindow_UI,self).__init__()
        self.initUI()

    def initUI(self):
        print('initUI')
        ## set font and color
        self.font1 = QFont('Arial',20,50)   # family size bold
        self.color_white = QPalette()
        self.color_white.setColor(QPalette.Window, Qt.white)
        
        ## channel control
        self.list_edit_label = []
        self.list_button_enable = []
        self.list_spinbox_freq = []
        self.list_spinbox_amp = []
        self.list_spinbox_phase = []
        self.glay_channels = QGridLayout()
        self.channels()

        ## save file
        self.combo_com = QComboBox()
        self.button_connect = QPushButton('Connect')
        self.button_load = QPushButton('Load')
        self.button_save = QPushButton('Save')
        self.edit_file = QTextEdit()
        self.glay_file = QGridLayout()
        self.configFile()

        ## frequency ramp mode extension
        self.button_fm = QPushButton('>')
        self.button_fm.setFixedSize(15,196)
        self.button_fm.setCheckable(True)
        self.button_fm.clicked.connect(self.showFrWidget)
        self.widget_fm = QWidget()

        self.list_button_fm_enable = []
        self.list_button_fm_set = []
        self.list_spinbox_freq_range = []
        self.list_spinbox_freq_step = []
        self.list_spinbox_scan_time = []
        self.glay_fm = QGridLayout()
        self.freqModulation()
        self.widget_fm.setLayout(self.glay_fm)
        self.widget_fm.hide()

        ## status bar
        self.bar_status = QStatusBar()
        self.bar_status.showMessage('DDS control.')

        ## main layout
        self.setStatusBar(self.bar_status)
        self.glay_main = QGridLayout()
        self.glay_main.addLayout(self.glay_channels,0,0)
        self.glay_main.addLayout(self.glay_file,1,0)
        self.glay_main.addWidget(self.button_fm,0,1)
        self.glay_main.addWidget(self.widget_fm,0,2)
        self.glay_main.setSizeConstraint(QLayout.SetFixedSize)

        ## main widget
        self.widget = QWidget()
        self.widget.setLayout(self.glay_main)
        self.setCentralWidget(self.widget)
        self.move(200,200)
        #QApplication.processEvents()    
        QApplication.processEvents() 
        self.setFixedSize(self.minimumSizeHint())
        self.setWindowTitle('DDS Control')
        self.show()

    def channels(self):
        ## initialize channel parameter widgets
        ## frequency/MHz: range 0-1GHz
        ## amplitude/V: range depends on DDS itself, here 1V
        ## phase/degree: range 0 ~ 360
        self.glay_channels.addWidget(QLabel('Label'),0,0)
        self.glay_channels.addWidget(QLabel('On/Off'),0,1)
        self.glay_channels.addWidget(QLabel('Frequency (MHz)'),0,2)
        self.glay_channels.addWidget(QLabel('Amplitude'),0,3)
        self.glay_channels.addWidget(QLabel('Phase (degree)'),0,4)
        for i in range(4):
            edit_label = QLineEdit()
            edit_label.setFont(self.font1)
            edit_label.setFixedWidth(100)
            self.list_edit_label.append(edit_label)
            self.glay_channels.addWidget(self.list_edit_label[i],i+1,0)

            button_enable = QPushButton()
            button_enable.setCheckable(True)
            button_enable.setFont(self.font1)
            button_enable.setFixedSize(40,40)
            button_enable.setStyleSheet("QPushButton{border: 1px solid;background-color:white;} QPushButton:checked{border:5px inset white;background-color:green;}")
            self.list_button_enable.append(button_enable)
            self.glay_channels.addWidget(self.list_button_enable[i],i+1,1)

            spinbox_freq = QDoubleSpinBox()
            spinbox_freq.setRange(0,1e3) #MHz
            spinbox_freq.setSingleStep(1)
            spinbox_freq.setDecimals(6)     # set frequency precision to 0.1Hz , the actual value is 0.23Hz at 1GHz sample
            spinbox_freq.setValue(10)
            spinbox_freq.setFont(self.font1)
            self.list_spinbox_freq.append(spinbox_freq)
            self.glay_channels.addWidget(self.list_spinbox_freq[i],i+1,2)

            spinbox_amp = QDoubleSpinBox()
            spinbox_amp.setRange(0,1) #Unit
            spinbox_amp.setSingleStep(0.01)
            spinbox_amp.setDecimals(3)
            spinbox_amp.setValue(0)
            spinbox_amp.setFont(self.font1)
            self.list_spinbox_amp.append(spinbox_amp)
            self.glay_channels.addWidget(self.list_spinbox_amp[i],i+1,3)

            spinbox_phase = QDoubleSpinBox()
            spinbox_phase.setRange(0,360) #degree
            spinbox_phase.setSingleStep(1)
            spinbox_phase.setDecimals(2)
            spinbox_phase.setValue(0)
            spinbox_phase.setFont(self.font1)
            self.list_spinbox_phase.append(spinbox_phase)
            self.glay_channels.addWidget(self.list_spinbox_phase[i],i+1,4)
        self.glay_channels.setRowStretch(5,1)
        self.glay_channels.setContentsMargins(0,0,0,0)

    def configFile(self):
        self.combo_com.setFixedSize(80,20)
        #self.combo_com.setAutoFillBackground(True)
        #self.combo_com.setPalette(self.color_white)
        self.button_load.setFixedSize(40,20)
        self.button_save.setFixedSize(40,20)
        self.edit_file.setFixedHeight(50)
        self.glay_file.addWidget(self.combo_com,0,0)
        self.glay_file.addWidget(self.button_connect,1,0)
        self.glay_file.addWidget(self.button_load,0,1)
        self.glay_file.addWidget(self.button_save,1,1)
        self.glay_file.addWidget(self.edit_file,0,2,0,1)
        
    def showFrWidget(self):
        if self.button_fm.isChecked():
            self.widget_fm.show()
            self.button_fm.setText('<')
        else:
            self.widget_fm.hide()
            self.button_fm.setText('>')
        #QApplication.processEvents()    
        QApplication.processEvents()    
        self.setFixedSize(self.minimumSizeHint())

    def freqModulation(self):
        self.glay_fm.addWidget(QLabel('FM On/Off'),0,0)
        self.glay_fm.addWidget(QLabel('FM Set'),0,1)
        self.glay_fm.addWidget(QLabel('Freq range (MHz)'),0,2)
        self.glay_fm.addWidget(QLabel('Freq step (MHz)'),0,3)
        self.glay_fm.addWidget(QLabel('Scan time (s)'),0,4)
        for i in range(4):
            button_fm_enable = QPushButton("OFF")
            button_fm_enable.setCheckable(True)
            button_fm_enable.setFont(self.font1)
            self.list_button_fm_enable.append(button_fm_enable)
            self.glay_fm.addWidget(self.list_button_fm_enable[i],i+1,0)

            button_fm_set = QPushButton("SET")
            button_fm_set.setFont(self.font1)
            self.list_button_fm_set.append(button_fm_set)
            self.glay_fm.addWidget(self.list_button_fm_set[i],i+1,1)

            spinbox_freq_range = QDoubleSpinBox()
            spinbox_freq_range.setRange(0,1e3) #MHz
            spinbox_freq_range.setSingleStep(1)
            spinbox_freq_range.setDecimals(7)     # set frequency precision to 0.1Hz , the actual value is 0.23Hz at 1GHz sample
            spinbox_freq_range.setValue(10)
            spinbox_freq_range.setFont(self.font1)
            self.list_spinbox_freq_range.append(spinbox_freq_range)
            self.glay_fm.addWidget(self.list_spinbox_freq_range[i],i+1,2)

            spinbox_freq_step = QDoubleSpinBox()
            spinbox_freq_step.setRange(0,1e3) #MHz
            spinbox_freq_step.setSingleStep(1)
            spinbox_freq_step.setDecimals(7)
            spinbox_freq_step.setValue(0.001)
            spinbox_freq_step.setFont(self.font1)
            self.list_spinbox_freq_step.append(spinbox_freq_step)
            self.glay_fm.addWidget(self.list_spinbox_freq_step[i],i+1,3)

            spinbox_scan_time = QDoubleSpinBox()
            spinbox_scan_time.setRange(0,2) #second
            spinbox_scan_time.setSingleStep(0.1)
            spinbox_scan_time.setDecimals(2)
            spinbox_scan_time.setValue(1)
            spinbox_scan_time.setFont(self.font1)
            self.list_spinbox_scan_time.append(spinbox_scan_time)
            self.glay_fm.addWidget(self.list_spinbox_scan_time[i],i+1,4)

        self.glay_fm.setRowStretch(5,1)       
        self.glay_fm.setContentsMargins(0,0,0,0)


        


if __name__ == '__main__':
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication([])
    
    window = MainWindow_UI()
    sys.exit(app.exec_())

    

        