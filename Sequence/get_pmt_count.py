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
        self.pmt = self.get_device('ttl0')

    @kernel
    def run_sequence(self):
        # initialize dds
        #count = np.zeros(1000,dtype=bool)
        self.core.break_realtime()
        
        self.pmt.gate_rising(400*us)
        photon_count = self.pmt.count(now_mu())
        
        return photon_count

    def run(self):
        photon_count = self.run_sequence()
        print('pmt count:%d' % photon_count)