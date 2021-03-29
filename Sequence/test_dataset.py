
from artiq.experiment import *
import numpy as np
import time


class test(EnvExperiment):
    def build(self):
        self.setattr_device('core')

    @kernel
    def run(self):
        self.set_dataset("test",np.full(100,0),broadcast=True)
        for i in range(100):
            self.mutate_dataset("test",i,i*i)
            print('over')

