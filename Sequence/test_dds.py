
# DDS frequency test

import time
from artiq.experiment import *

class DDS_test(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]

        self.detection = self.get_device(dds_channel[0])
    
    
    @kernel
    def run(self):

        # asf = amp/1*2**14
        # fre = fre/1GHz*2**32
        self.detection.init()

        self.core.break_realtime()
    
        asf = self.detection.amplitude_to_asf(0.5)
        fre = self.detection.frequency_to_ftw(240*MHz)

        # ram_asf = self.detection.amplitude_to_ram(0.5)
        # ram_fre = self.detection.frequency_to_ram(240*MHz)
        #print("amp：%s, fre:%s" % (asf,fre))
        # print("ram amp:%s, ram fre:%s" % (ram_asf, ram_fre))
        
        # set profile
        delay(30*ms)
        self.detection.set(frequency=240*MHz,amplitude=0.5, profile=0)
        
        self.detection.set(frequency=250*MHz,amplitude=0.5, profile=1)
        self.detection.set(frequency=260*MHz,amplitude=0.5, profile=2)
        self.detction.read16(20)