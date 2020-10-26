import sys, os
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


fre = 250

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.dds2 = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')

    @kernel
    def set_dds(self):
        # initialize dds
        #count = np.zeros(1000,dtype=bool)
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.dds2.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(19.4) 
        self.cooling.set_att(25.)  
        self.pumping.set_att(19.)

        self.cooling.sw.off()
        self.detection.sw.off()
        self.dds2.sw.off()
        
        self.pumping.sw.on()

    def run(self):
        print('set frequecny %d' % fre)
        self.set_dds()