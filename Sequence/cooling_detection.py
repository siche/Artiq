# usage:
# This sequence will:
# 1. Cooling---> 2. Pumping --> 3. Detection(using cooling light)
# It can be used to:
# 1. Check cooling result
# 2. Check background count when turn off 935

import sys,os,select,time
import numpy as np
from artiq.experiment import *
from tqdm import trange
import matplotlib.pyplot as plt

if os.name == "nt":
    import msvcrt

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')

        # DDS port
        self.dds935 = self.get_device(dds_channel[0])
        self.light = self.get_device(dds_channel[1])
        self.dds435 = self.get_device(dds_channel[2])

        # Rf switch
        self.pmt = self.get_device('ttl0')
        self.coolingSwitch = self.get_device('ttl4')
        self.repumpingSwitch = self.get_device('ttl5')
        self.pumpingSwitch = self.get_device('ttl6')
        self.rabiSwitch = self.get_device('ttl7')

    @kernel
    def run_sequence(self, repeat_time = 100):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()

        self.light.cpld.set_profile(0)
        delay(2*us)
        self.light.sw.on()
        delay(2*us)
        self.dds935.sw.on()
        delay(2*us)

        with parallel:
            self.coolingSwitch.on()
            self.pumpingSwitch.off()
            self.repumpingSwitch.on()
    
        photon_count = 0
        photon_number = 0
        count = 0

        for i in range(repeat_time):
            with sequential:

                # cooling for 1.5 ms
                self.light.sw.on()
                delay(1*ms)
                self.light.cpld.set_profile(1)
                delay(2*us)

                # detection on
                with parallel: 
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
               
        self.light.cpld.set_profile(0)
        delay(2*us)
        return (count,photon_count)

    def run(self):

        N = 100
        R = 100
        data = np.zeros((3,N))
        for i in trange(N):
            temp = self.run_sequence(repeat_time=R)
            data[0,i]= i
            data[1,i]=temp[0]*100/R
            data[2,i]=temp[1]
            print("%d/%d" %((i+1),N))
            print('cout:%d\neffiency:%d%%' % (temp[1],temp[0]))
        

        plt.figure(1)
        ax1 = plt.subplot(121)
        ax1.plot(data[0],data[1])
        ax1.set_title('Detection Effiency')

        ax2 = plt.subplot(122)
        ax2.plot(data[0],data[2])
        ax2.set_title('Detection Count')
        plt.show()
