import sys
import os
import select
import numpy as np
from artiq.experiment import *
import matplotlib.pyplot as plt


if os.name == "nt":
    import msvcrt


class KasliTester(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        self.ttl_435 = self.get_device('ttl7')

    @kernel
    def pre_set(self):
        # initialize dd        
        self.core.break_realtime()

    @kernel
    def run_sequence(self):
        self.core.break_realtime()
        with sequential:
            self.ttl_435.on()
    

    def run(self):
        self.pre_set()
        self.run_sequence()
