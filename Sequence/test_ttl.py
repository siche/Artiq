import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


class KasliTester(EnvExperiment):
    def build(self):
        # dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.ttl_435 = self.get_device('ttl6')

    @kernel
    def ttl_on(self):
        self.core.break_realtime()
        with sequential:
            self.ttl_435.off()
            delay(500*ms)

    @kernel
    def ttl_off(self):
        self.core.break_realtime()
        self.ttl_435.on()
        

    def run(self):

        for i in range(10):
            self.ttl_on()
