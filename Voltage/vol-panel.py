from PyQt5.QtWidgets import QApplication,QWidget,QGridLayout,QLineEdit,QDoubleSpinBox,QPushButton,QMessageBox,QLabel
from PyQt5 import QtCore,QtWidgets,QtGui
import sys
import os 

class vol_panel(QWidget):

    def __init__(self,parent=None):
        super(vol_panel,self).__init__()
        self.initUi()

    def initUi(self):
        init_vol1 = [5,1,-0.7,1,5]
        init_vol2 = [5,1,-0.33,1,5]
        layout = QGridLayout()
        for i in range(5):
            var1 = 'vol1'+str(i+1)
            var2 = 'vol2'+str(i+1)

            exec(var1+'=QDoubleSpinBox()')
            exec(var2+'=QDoubleSpinBox()')

            l11 = var1+'.setRange(-10,10)'
            l21 = var2+'.setRange(-10,10)'

            l12 = var1+'.setDecimals(2)'
            l22 = var2+'.setDecimals(2)'

            l13 = var1+'.setValue('+str(init_vol1[i])+')'
            l23 = var2+'.setValue('+str(init_vol2[i])+')'

            l14 = var1+'.setSingleStep(0.01)'
            l24 = var2+'.setSingleStep(0.01)'

            line1 = [l11,l12,l13,l14]
            line2 = [l21,l22,l23,l24]

            for k in range(4):
                exec(line1[k])
                exec(line2[k])
            
            add_code1 = 'layout.addWidget('+var1+',1,'+str(i+1)+')'
            add_code2 = 'layout.addWidget('+var2+',2,'+str(i+1)+')'
            eval(add_code1)
            eval(add_code2)
            #eval(add_code2)

            
            add_attr1 = 'self.'+var1+'='+var1
            add_attr2 = 'self.'+var2+'='+var2
            exec(add_attr1)
            exec(add_attr2)

        btn = QPushButton('Apply')
        btn.clicked.connect(self.set_value)

        layout.addWidget(btn,3,2)
        l1 = QLabel('Left')
        l2 = QLabel('Right')
        layout.addWidget(l1,1,0)
        layout.addWidget(l2,2,0)

        self.setLayout(layout)
        self.message = QMessageBox()

    def set_value(self):
        # print(self.vol11)
        vol1 = [0]*5
        vol2 = [0]*5
        for k in range(2):
            for i in range(5):
                code = 'vol'+str(k+1)+'['+str(i)+']=self.vol'+str(k+1)+str(i+1)+'.value()'
                exec(code)
        vol = vol1+vol2
        new_vol = 'vol = '+str(vol)
        
        #self.message.setText('确定设置此电压?')
        #self.message.exec_()
        f=open('vol-template.py','r')
        con = f.read()
        con1 = con.replace('vol = [5.0,1.,-0.75,1.,5.0]+[5.,1.,-0.35,1.,5.]',new_vol)
        f.close()
        f = open('set_voltage.py','w')
        f.write(con1)
        f.close()

        os.system('set_voltage.bat')
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = vol_panel()
    ex.show()
    sys.exit(app.exec_())