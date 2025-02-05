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
        self.ttl_935 = self.get_device('ttl7')

    @kernel
    def pre_set(self):
        # initialize dd        

        self.core.break_realtime()

    @kernel
    def run_sequence(self):
        self.core.break_realtime()
        with sequential:
            self.ttl_935.off()
            delay(0.5*s)
            self.ttl_935.on()
            delay(0.5*s)

    def run(self):
        self.pre_set()
        for i in range(100):
            self.run_sequence()
