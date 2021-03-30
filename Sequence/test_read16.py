from artiq.experiment import *

class RW16Test(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.dev = self.get_device("urukul0_ch0")

    def run(self):
        self.run_test()

    @kernel
    def run_test(self):
        a = [0]*100
        for i in range(100):
            a[i] = i*i
        self.run_list(a)

    @rpc(flags={"async"})
    def run_list(self, x):
        for i in range(len(x)):
            print(x[i])