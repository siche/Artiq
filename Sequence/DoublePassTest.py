import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


fre = 255

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')

        # DDS port
        self.dds935 = self.get_device(dds_channel[0])
        self.light = self.get_device(dds_channel[1])
        self.dds435 = self.get_device(dds_channel[2])

        # Rf switch
        self.pmt = self.get_device('ttl0')
        self.coolingSwitch = self.get_device('ttl4')
        self.repumpingSwitch = self.get_device('ttl5')
        self.pumpingSwitch = self.get_device('ttl6')
        self.rabiSwitch = self.get_device('ttl7')


    @kernel
    def run(self):

        # Initialize dds and switch
        self.core.reset()
        delay(10*ms)
        self.core.break_realtime()
    
        # Initialize DDS
        self.light.init()
        self.dds935.init()
        # self.dds435.init()
        
        self.light.cpld.set_profile(0)
        delay(2*us)
        self.light.set(260*MHz, amplitude = 0.5, profile=0)
        delay(2*us)
        self.light.set(260*MHz, amplitude = 0.5, profile=1)
        delay(2*us)
        
        self.dds935.set(80*MHz, profile=0)
        delay(2*us)

        self.dds935.set(80*MHz, profile=1)
        delay(2*us)
        self.dds435.set(240*MHz, profile=0)
        delay(2*us)
        self.dds435.set(280*MHz, profile=1)
        delay(2*us)

        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的
        self.light.set_att(18.8)     # = -6.60dbm
        self.dds935.set_att(20.)
        self.dds435.set_att(20.0)
        
        #turn off all DDS except light
        
        self.light.sw.on()
        self.dds935.sw.on()
        self.dds435.sw.on()

        # turn on related rf 
        delay(2*us)
        self.coolingSwitch.on()
        delay(2*us)
        self.repumpingSwitch.on()
        delay(2*us)
        self.pumpingSwitch.off()
        delay(2*us)

        