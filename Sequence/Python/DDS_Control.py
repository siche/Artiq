import sys
from functools import partial
import serial.tools.list_ports
import json

from DDS_UI import MainWindow_UI
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from DDS import DDS_AD9910


class MainWindow(MainWindow_UI):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.dds_config = []
        self.initEvents()   
        self.initVars()

    def initEvents(self):
        for i in range(4):
            self.list_button_enable[i].clicked.connect(partial(self.chOnOff ,i))
            self.list_spinbox_freq[i].valueChanged.connect(partial(self.chFreq, i))
            self.list_spinbox_amp[i].valueChanged.connect(partial(self.chAmp, i))
            self.list_spinbox_phase[i].valueChanged.connect(partial(self.chPhase, i))
            self.list_button_fm_enable[i].clicked.connect(partial(self.chFmEnable,i))
            self.list_button_fm_set[i].clicked.connect(partial(self.chFmSet,i))
        self.button_connect.clicked.connect(self.serialConnect)
        self.button_load.clicked.connect(self.loadConfig)
        self.button_save.clicked.connect(self.saveConfig)

    def initVars(self):
        self.bar_status.showMessage('Get available serial port.')
        list_port = list(serial.tools.list_ports.comports())
        self.name_port = []
        for i in range(len(list_port)):
            temp = list_port[i]
            self.name_port.append(temp[0])
        #dds_com = 'COM3'    # serial port of dds, you can change it here
        self.combo_com.addItems(self.name_port) 
        self.combo_com.setCurrentIndex(1) 
        #self.combo_com.addItem('COM3')
        #self.dds = DDS_AD9910(self.combo_com.text(),dds_ports=[0,1,2,3])
        self.dds = DDS_AD9910(dds_ports=[0,1,2,3])
        #self.dds = DDS_AD9910(dds_ports=[0,1,2])
        

    def serialConnect(self):
        if len(self.dds.com_port) == 0:
            self.bar_status.showMessage('Connect to DDS...')
            if not self.dds.open(self.combo_com.currentText()):
                self.bar_status.showMessage('Connected to DDS.')
        else:
            # re-connnect to the dds will first close the connected dds
            # this can be used to re-initialized the dds
            self.bar_status.showMessage('Re-connect to DDS...')
            self.dds.close()
            if not self.dds.open(self.combo_com.currentText()):
                self.bar_status.showMessage('Connected to DDS.')

    def chOnOff(self, ch):
        if self.list_button_enable[ch].isChecked():
            self.bar_status.showMessage('DDS control: channel '+str(ch)+' opend.')
            self.dds.setOnOff(ch,True)
        else:
            self.bar_status.showMessage('DDS control: channel '+str(ch)+' closed.')
            self.dds.setOnOff(ch,False)
        self.list_button_enable[ch].blockSignals(True)
        onoff = self.dds.getOnOff(ch)
        self.list_button_enable[ch].setChecked(onoff)
        self.list_button_enable[ch].blockSignals(False)

    def chFreq(self, ch):
        freq = self.list_spinbox_freq[ch].value()
        self.bar_status.showMessage('DDS control: channel '+str(ch)+' frequency changed to '+str(freq)+' MHz.')
        self.dds.setFrequency(ch,freq)
        self.list_spinbox_freq[ch].blockSignals(True)
        freq = self.dds.getFrequency(ch)
        self.list_spinbox_freq[ch].setValue(freq)
        self.list_spinbox_freq[ch].blockSignals(False)

    def chAmp(self, ch):
        amp = self.list_spinbox_amp[ch].value()
        self.bar_status.showMessage('DDS control: channel '+str(ch)+' amplitude changed to '+str(amp)+'.')
        self.dds.setAmplitude(ch,amp)
        self.list_spinbox_amp[ch].blockSignals(True)
        amp = self.dds.getAmplitude(ch)
        self.list_spinbox_amp[ch].setValue(amp)
        self.list_spinbox_amp[ch].blockSignals(False)

    def chPhase(self, ch):
        phase = self.list_spinbox_phase[ch].value()
        self.bar_status.showMessage('DDS control: channel '+str(ch)+' phase changed to '+str(phase)+' degree.')
        self.dds.setPhase(ch,phase)        
        self.list_spinbox_phase[ch].blockSignals(True)
        phase = self.dds.getPhase(ch)
        self.list_spinbox_phase[ch].setValue(phase)
        self.list_spinbox_phase[ch].blockSignals(False)

    def loadConfig(self):
        file_choose = QFileDialog.getOpenFileName(self,'Open a config file','./','*.json')
        file_name = file_choose[0]
        self.dds_config = []
        if file_name != '':
            self.edit_file.setText(file_name)
            #print(file_name)
            try:
                fid = open(file_name,'r')
                config_json = json.load(fid)
            except IOError:
                self.bar_status.showMessage('Open file error.')
            else:
                print('Load dds config file: ',file_name)
                for i in range(4):
                    dds_name = 'dds'+str(i)
                    this_dds = config_json[dds_name]
                    self.dds_config.append(this_dds)
                    self.list_edit_label[i].setText(this_dds['label'])
                    onoff = this_dds['output']
                    self.list_button_enable[i].setChecked(onoff)
                    freq = this_dds['frequency']
                    self.list_spinbox_freq[i].setValue(freq)
                    amp = this_dds['amplitude']
                    self.list_spinbox_amp[i].setValue(amp)
                    phase = this_dds['phase']
                    self.list_spinbox_phase[i].setValue(phase)
                    self.dds.setAll(i,onoff,freq,amp,phase)
                    onoff,freq,amp,phase = self.dds.getAll(i)
                    self.list_button_enable[i].blockSignals(True)
                    self.list_button_enable[i].setChecked(onoff)
                    self.list_button_enable[i].blockSignals(False)
                    self.list_spinbox_freq[i].blockSignals(True)
                    self.list_spinbox_freq[i].setValue(freq)
                    self.list_spinbox_freq[i].blockSignals(False)
                    self.list_spinbox_amp[i].blockSignals(True)
                    self.list_spinbox_amp[i].setValue(amp)
                    self.list_spinbox_amp[i].blockSignals(False)
                    self.list_spinbox_phase[i].blockSignals(True)
                    self.list_spinbox_phase[i].setValue(phase)
                    self.list_spinbox_phase[i].blockSignals(False)
                #print(self.dds_config)
                fid.close()
                self.bar_status.showMessage('Load dds config file.')
                   
    def saveConfig(self):
        file_choose = QFileDialog.getSaveFileName(self,'Open a config file','./','*.json')
        file_name = file_choose[0]
        if file_name != '':
            self.edit_file.setText(file_name)
            #print(file_name)
            try:
                fid = open(file_name,'w')
            except IOError:
                self.bar_status.showMessage('Open file error.')
            else:
                config_json = {}
                for i in range(4):
                    config_json['dds'+str(i)] = {
                        "label":self.list_edit_label[i].text(),
                        "output":self.list_button_enable[i].isChecked(),
                        "frequency":self.list_spinbox_freq[i].value(),
                        "amplitude":self.list_spinbox_amp[i].value(),
                        "phase":self.list_spinbox_phase[i].value(),
                        "fm_mod":{
                            "mod_enbale":False,
                            "mod_freq_range":10.000000,
                            "mod_freq_step":0.001000,
                            "scan_time":1.00
                        }
                    }
                print(config_json)
                json.dump(config_json,fid,indent=4)
                fid.close()
                self.bar_status.showMessage('Save dds config file.')

    def chFmEnable(self,ch):
        if self.list_button_fm_enable[ch].isChecked():
            self.list_button_fm_enable[ch].setText('ON')
            self.bar_status.showMessage('DDS control: channel ' + str(ch)+' frequency modulation enabled.')
            self.dds.setMode(ch,'Freq ramp mod')
        else:
            self.list_button_fm_enable[ch].setText('OFF')
            self.bar_status.showMessage('DDS control: channel ' + str(ch)+' frequency modulation disabled.')
            self.dds.setMode(ch,'Single tune')

    def chFmSet(self,ch):
        freq_up = self.list_spinbox_freq[ch].value() + self.list_spinbox_freq_range[ch].value()
        freq_down = self.list_spinbox_freq[ch].value() - self.list_spinbox_freq_range[ch].value()
        freq_step = self.list_spinbox_freq_step[ch].value()
        scan_time = self.num_scan_time[ch].value()
        self.bar_status.showMessage('DDS control: channel '+str(ch)+' frequency modulation parameters set.')
        self.dds.setFreqRamp(ch,freq_up,freq_down,freq_step,scan_time)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'DDS Control',
                    "Sure to close DDS control?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.bar_status.showMessage('Close.')
            event.accept()
            self.dds.close()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication([])
        
    window = MainWindow()
    sys.exit(app.exec_())

