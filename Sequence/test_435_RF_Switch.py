
# DDS frequency test

import time
from artiq.experiment import *

class DDS_test(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]

        self.dds1_435 = self.get_device(dds_channel[2])
        
    
    @kernel
    def run(self):

        # asf = amp/1*2**14
        # fre = fre/1GHz*2**32
        self.core.break_realtime()
        self.dds1_435.init()
        delay(2*ms)
        self.dds1_435.set(250*MHz)
        self.dds1_435.set_att(0.0)

        self.dds1_435.sw.on()


