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
        self.ttl = self.get_device('ttl4')

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.microwave.init()
        
        # set frequecny
        
        
        self.microwave.set(150*MHz)
        # set amplitude attenuation
        # the origin output is about 9 dbm( equal to set_att(0.))
        # the attenuation number must be float like 0. whose unit is dB
        # dds 不是连续的

        self.microwave.set_att(19.)
        # self.microwave.set_att(0.5)     # = 0dbm

        #turn off all DDS
        self.microwave.sw.off()
        for i in range(1000):
            self.ttl.on()
            delay(10*ms)
            self.ttl.off()
            delay(10*ms)

        # turn off microwave 
        # turn on ttl making LB1005 work
        self.microwave.sw.off()
        self.ttl.on()
            
    
    def run(self):
        self.set_dds()