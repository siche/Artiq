import sys
import os
import select
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
        self.dds3 = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.dds2.init()
        self.dds3.init()

        # set frequecny
        
        self.cooling.set(fre*MHz)
        self.detection.set(240*MHz, amplitude = 0.2, profile=0)
        self.dds2.set(400*MHz)
        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的

        self.detection.set_att(19.4)  # = -8.74dbm
        self.cooling.set_att(20.)     # = -6.60dbm
        
        #turn off all DDS except cooling
        self.dds2.sw.off()
        self.dds3.sw.off()

        self.cooling.sw.on()
        self.detection.sw.off()
        self.dds3.sw.off()
        

    def run(self):
        print('set cooling frequecny %d' % fre)
        self.set_dds()
        """
        for i in range(4):
            self.detection.set_profile(0)
            delay(5*s)
        """