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
        
        photon_count = 0
        event_count = 0

        for i in range(1000):
            delay(10*us)
            self.pmt.gate_rising(400*us)
            photon_number = self.pmt.count(now_mu())
            if photon_number:
                photon_count += photon_number
                event_count += 1
            
    
        return (photon_count, event_count)

    def run(self):
        for i in range(1000):
            (photon_count, event_count) = self.run_sequence()
            print('\rpmt count:%d, efficiency:%1.2f%%' % (photon_count, event_count/10), end=" ")