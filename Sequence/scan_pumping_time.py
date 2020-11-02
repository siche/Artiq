# usage:
# This sequence will:
# 1. Cooling---> 2. Pumping --> 3. Detection(using cooling light)
# It can be used to:
# 1. Check cooling result
# 2. Check background count when turn off 935

import sys
import os
import select
import numpy as np
from artiq.experiment import *
from scipy.optimize import curve_fit
from save_data import save_file
from progressbar import *
import matplotlib.pyplot as plt

import time
from save_data import save_file
if os.name == "nt":
    import msvcrt

def fit_func(x,a,b,c,d):
    return a*np.sin(b*x+c)+d

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')
        self.ttl_935 = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

    @kernel
    def run_sequence(self,pumping_time = 400.0):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.microwave.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)
        self.microwave.set(400.*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(19.4) 
        self.cooling.set_att(19.)
        self.microwave.set_att(0.)
        self.pumping.set_att(25.)

        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        for i in range(100):
            with sequential:
                
                self.detection.sw.off()
                
                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(1.5*ms)
                self.cooling.sw.off()

                # pumping
                self.pumping.sw.on()
                delay(pumping_time*us)
                self.pumping.sw.off()
                

                # detection on
                with parallel: 
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.detection.sw.on()
                    # delay(10)
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
               
                self.detection.sw.off()
        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()

        return (count,photon_count)

    def run(self):
        
        # dds_435 = dds_controller()
        # flip_time = 75
        # microwave_fre = 400.0
        init_time = 1.
        time_interval = 0.5
        N = 40
        data = np.zeros((3,N))
        for i in range(N):
            pumping_time = init_time+time_interval*i
            # pumping_time = 15.0
            temp = self.run_sequence(pumping_time)
            data[0,i]=pumping_time
            data[1,i]=temp[0]*2
            data[2,i]=temp[1]
            print("%d/%d" %((i+1),N))
            print('cout:%d\neffiency:%d%%' % (temp[1],temp[0]))
        

        save_file(data,__file__[:-3])
        plt.figure(1)
        ax1 = plt.subplot(121)
        ax1.plot(data[0],data[1])
        ax1.set_title('Detection Effiency')

        ax2 = plt.subplot(122)
        ax2.plot(data[0],data[2])
        ax2.set_title('Detection Count')
        plt.show()
