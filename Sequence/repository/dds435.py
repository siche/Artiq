import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


fre = 239.9458

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.dds2 = self.get_device(dds_channel[2])

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.dds2.init()
        # set frequecny
        self.dds2.set_att(20.0)
        self.dds2.set(fre*MHz)
        self.dds2.sw.on()
        

    def run(self):
        print('set cooling frequecny %d' % fre)
        self.set_dds()
        """
        for i in range(4):
            self.detection.set_profile(0)
            delay(5*s)
        """