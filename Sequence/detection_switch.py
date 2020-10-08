import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt


class KasliTester(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        self.detection_switch = self.get_device('ttl4')

    @kernel
    def ttl_switch(self, switch_time=400):
        self.core.break_realtime()
        for i in range(1):
            with sequential:
                self.detection_switch.on()
                delay(switch_time*ms)
                self.detection_switch.off()
                delay(switch_time*ms)
                
    def run(self):
        for i in range(10):
            self.ttl_switch(500)
       # self.set_dds()
