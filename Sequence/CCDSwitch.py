from artiq.experiment import *
import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt

chs = [0, 2, 3, 4, 5, 8, 11, 12, 14, 15, 18, 20]

class CCDSwitch(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        self.setattr_device('zotino0')
    
    @kernel
    def run(self):
        self.core.break_realtime()
        self.zotino0.init()
        delay(10*ms)
        self.zotino0.write_dac(30,5.0)
        delay(10*ms)
        self.zotino0.load()