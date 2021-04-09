import sys
import os
import select
import numpy as np
import time

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


fre = 240

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.dds_435 = self.get_device(dds_channel[2])

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.dds_435.init()
       
        # set frequecny
        self.dds_435.set(240*MHz,amplitude=1.0)
        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的

        self.dds_435.set_att(20.0)  # = -8.74dbm
        
        #turn off all DDS except cooling
        self.dds_435.sw.on()
        

    @kernel
    def set_dds2(self):
        self.core.break_realtime()
        self.dds_435.init()
        self.dds_435.set(250*MHz)

    def run(self):
        print('set cooling frequecny %d' % fre)
        self.set_dds()
        time.sleep(5)
        self.set_dds2()
        """
        for i in range(4):
            self.detection.set_profile(0)
            delay(5*s)
        """