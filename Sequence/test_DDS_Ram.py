
from artiq.coredevice.ad9910 import (
    RAM_DEST_FTW, RAM_MODE_RAMPUP)
from artiq.experiment import *
from artiq.language import ns, us, ms, MHz
import logging
import numpy as np


logger = logging.getLogger()

class FreqRam_test(EnvExperiment):
    """Freq_RAM_AD9910_TEST_minimal"""
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl4") # used for measure the delay time of DDS setting
        self.setattr_device("scheduler")
        self.dds = self.get_device("urukul0_ch0")
        self.setattr_argument("time_step",
                              NumberValue(100.0, min=0.005, max=262, ndecimals=3))  
                              # time step for the frequency RAM, the maxium value is limited by 16 bit value,that is 2^16*4ns
  
    def prepare(self):
        # prepare frequency array
        freq1 = [10e6,100e6,200e6]
        self.data1 =np.full(3,1)
        self.dds.frequency_to_ram(freq1,self.data1)
        # prepare time step array
        # in units of 4ns: 100us, 200us, 1ms, 100ms, 10s
        # for a 16-bit integer, the last 3 values should be max value of around 260us
        self.steps = np.array([25000, 50000, 250000, 25000000, 10**10])


    @kernel
    def run(self):
        self.core.break_realtime()
        self.dds.sw.off()
        self.dds.set_amplitude(1.0)
        self.dds.set_att(0.0)
        for t in range(len(self.steps)):
            self.run_ram(self.steps[t])
        
       
    @kernel
    def run_ram(self, timestep_mu):
        # prepare ram
        delay(5 * us)
        self.dds.set_cfr1(ram_enable=0)
        self.dds.cpld.io_update.pulse_mu(8)
        self.dds.set_profile_ram(start=0, end=2, step=timestep_mu,
                                 profile=0, mode=RAM_MODE_RAMPUP)
        self.dds.cpld.set_profile(0)
        delay(10 * us) 
        self.dds.cpld.io_update.pulse_mu(8)
        delay(10 * us)
        self.dds.write_ram(self.data1)
        # prepare to enable ram and set frequency as target
        delay(10 * us)
        self.dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=RAM_DEST_FTW)
        # sent trigger and ramp for 1ms
        with parallel:
            self.dds.sw.on()
            self.ttl4.pulse(5 * us)
        self.dds.cpld.io_update.pulse_mu(8)
        delay(1 * ms)
        self.dds.set_cfr1(ram_enable=0)
        self.dds.sw.off()
 