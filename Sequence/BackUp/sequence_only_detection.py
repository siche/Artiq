import sys
import os
import select
import numpy as np
from artiq.experiment import *
import time
import matplotlib.pyplot as plt
# import pandas as pd

if os.name == "nt":
    import msvcrt

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')

    @kernel
    def run_sequence(self,t2):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.microwave.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)
        self.microwave.set(200.*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(19.4) 
        self.cooling.set_att(25.)
        self.microwave.set_att(0.)
        self.pumping.set_att(25.)

        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0

        count_data = [0]*1000
        for i in range(1000):
            with sequential:

                # cooling for 1 ms
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
               
                # pumping for 400us
                self.pumping.sw.on()
                delay(400*us)
                self.pumping.sw.off()

                # microwave on 400us
                self.microwave.sw.on()
                delay(t2*us)
                self.microwave.sw.off()

                # detection on
                with parallel: 
                    self.detection.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                count_data[i] = photon_number
                self.detection.sw.off()

        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()
        self.pumping.sw.off()
        
        return (count,photon_count,count_data)

    def run(self):
        data = self.run_sequence(125)
        print('efficiency:%.1f%%\nphoton count:%d' % (data[0]/10, data[1]))
        
        count_data = np.array(data[2])
        zero_data = count_data == 0
        print('zeros:%d' % zero_data.sum())
        plt.figure(1)
        plt.hist(data[2])
        print(data[2])
        plt.show()