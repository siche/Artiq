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
        self.setattr_device("ttl5")
        # self.ttl_435.output()

    @kernel
    def run(self):
        self.core.reset()

        self.ttl5.off()
            
    