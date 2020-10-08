import sys
import os
import select
import numpy as np
from artiq.experiment import *

import matplotlib.pyplot as plt
if os.name == "nt":
    import msvcrt

count_item = np.zeros((1000), dtype=np.int32)


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
    def run_sequence(self):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.microwave.init()
        self.pumping.init()

        self.cooling.set(248*MHz)
        self.detection.set((250+12)*MHz)
        self.microwave.set(400.*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(19.4)
        self.cooling.set_att(19.)
        self.microwave.set_att(0.)
        self.pumping.set_att(25.)

        self.microwave.sw.off()
        self.pumping.sw.off()

        with sequential:
            self.detection.sw.off()
            self.pumping.sw.off()
            # cooling for 1 ms
            self.cooling.sw.on()
            delay(1.5*ms)
            self.cooling.sw.off()
            delay(1*us)
            
            """
            # pumping for 400us
            self.pumping.sw.on()
            delay(30*us)
            self.pumping.sw.off()

            # microwave on
            self.microwave.sw.on()
            delay(27*us)
            self.microwave.sw.off()
            """
            # detection on
            with parallel:
                self.detection.sw.on()
                self.pmt.gate_rising(400*us)
                photon_number = self.pmt.count(now_mu())
            self.detection.sw.off()
            self.cooling.sw.on()

        # self.detection.sw.off()
        # self.microwave.sw.off()
        # self.pumping.sw.off()

        return photon_number

    def run(self):

        i = 0
        N = 100
        threshold = 1
        data = np.zeros((N),dtype=np.int)
        for i in range(N):
            temp = self.run_sequence()
            data[i] = temp
            print(i)
            print('count:%d' % temp)

        data1 = np.array(data) > threshold
        effiency = data1.sum()
        all_count = data[data1].sum()

        print(data)
        print('effiency:%.1f%%' % effiency)
        print('all count:%d' % all_count)

        plt.hist(data[data1],bins = 10, rwidth = 0.6)
        plt.show()
        
