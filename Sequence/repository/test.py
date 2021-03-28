from artiq.experiment import *
class MgmtTutorial(EnvExperiment):
    def build(self):
        self.setattr_argument("count", NumberValue(ndecimals=0, step=1))
    def run(self):
        for i in range(self.count):
            print("Hello World", i)