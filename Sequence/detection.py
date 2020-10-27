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
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.dds2 = self.get_device(dds_channel[2])
        self.dds3 = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')

    @kernel
    def set_dds(self):
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.dds2.init()
        self.dds3.init()

        # set frequecny
        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)

        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的

        self.detection.set_att(10.)
        self.cooling.set_att(25.)

        # turn off all DDS
        self.dds2.sw.off()
        self.dds3.sw.off()

        self.cooling.sw.off()

        for i in range(1000):
            with sequential:
                self.detection.sw.on()
                delay(0.5*s)
                self.detection.sw.off()
                delay(0.5*s)

    @kernel
    def set_dds_off(self):
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.dds2.init()
        self.dds3.init()

        # set frequecny
        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)

        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的

        self.detection.set_att(19.4)
        self.cooling.set_att(25.)

        # turn off all DDS
        self.dds2.sw.off()
        self.dds3.sw.off()

        self.cooling.sw.off()
        self.detection.sw.off()

    @kernel
    def set_dds_on(self):
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.dds2.init()
        self.dds3.init()

        # set frequecny
        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)

        # set amplitude attenuation
        # the origin output is about 9 dbm
        # the attenuation number must be float like 0.
        # dds 不是连续的

        self.detection.set_att(19.5)
        self.cooling.set_att(25.)

        # turn off all DDS
        self.dds2.sw.off()
        self.dds3.sw.off()

        self.cooling.sw.off()
        self.detection.sw.on()

    def run(self):
        self.set_dds_on()
       # self.set_dds()
