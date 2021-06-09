import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


fre1 = 241.893
fre2 = 243.432

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        # self.setattr_device("urukul0_ch")
        self.dds2 = self.get_device(dds_channel[2])

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.dds2.init()
        # set frequecny
        self.dds2.set_att(20.0)

        # profile
        self.dds2.set(fre1*MHz,amplitude = 1.0, profile=0)
        self.dds2.set(fre2*MHz,amplitude=0.8, profile=1)

        self.dds2.cpld.set_profile(0)
        self.dds2.sw.on()

        for i in range(10):
            delay(500*ms)
            self.dds2.cpld.set_profile((i+1)%2)
        
        self.dds2.cpld.set_profile(1)
        

    def run(self):
        self.set_dds()
        """
        for i in range(4):
            self.detection.set_profile(0)
            delay(5*s)
        """