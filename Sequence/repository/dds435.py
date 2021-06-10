import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


fre = 240.0

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.dds2 = self.get_device(dds_channel[2])

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        delay(10*ms)
        self.dds2.init()
        delay(10*ms)
        # set frequecny
        self.dds2.set_att(20.0)
        self.dds2.set_frequency(fre*MHz)
        self.dds2.sw.on()
        

    def run(self):
        print('set cooling frequecny %.3f' % fre)
        self.set_dds()
        """
        for i in range(4):
            self.detection.set_profile(0)
            delay(5*s)
        """