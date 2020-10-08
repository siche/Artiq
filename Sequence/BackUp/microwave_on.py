import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.microwave = self.get_device(dds_channel[2])

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.microwave.init()
        
        # set frequecny
        
        self.microwave.set(400*MHz)
        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的

        self.microwave.set_att(0.)     # = 0dbm

        #turn off all DDS
        self.microwave.sw.off()
        self.microwave.sw.on()
    
    def run(self):
        self.set_dds()