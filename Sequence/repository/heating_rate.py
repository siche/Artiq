import numpy as np
import time
from artiq.experiment import *
import matplotlib.pyplot as plt

_RED_SIDEBAND = 238.103
_BLUE_SIDEBAND = 241.103

class HeatingRateMeasurement(EnvExperiment):
    def build(self):

        # define HardWare device
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.dds1_435 = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])

        self.pmt = self.get_device('ttl0')
        self.ttl_935_AOM = self.get_device('ttl4')
        self.ttl_935_EOM = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

    def run(self):
        t1 = time.time()
        self.pre_set()
        self.sidebandcooling()
        t2 = time.time()
        print("time cost:%s" % (t2-t1))

    @kernel
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.dds1_435.init()
        self.microwave.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.dds1_435.set(_RED_SIDEBAND*MHz)
        self.microwave.set(400.*MHz)
        self.pumping.set(260*MHz)

        self.dds1_435.set_att(20.)
        self.cooling.set_att(10.)
        self.microwave.set_att(0.)
        self.pumping.set_att(18.)

        # define dataset
        # self.set_dataset("SBCData", np.full(100, 0), broadcast=True)

    @kernel
    def HeatingRate(self,delay_time=1, rabi_time = 20):
        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0

        temp_count = 0
        N = 100

        data_aom_frequency = [0]*100
        data_count = [0]*100

        for i in range(100):
            
            # set 435 aom frequency
            aom_scan_step = 0.001 
            AOM_435 = _RED_SIDEBAND + i*aom_scan_step
            self.dds1_435.set(AOM_435*MHz)
            
            temp_count = 0

            # 对于每一个frequency测量100次
            for j in range(100)
                with sequential:

                    # 0.0 doppler cooling
                    self.cooling.sw.on()
                    delay(1*ms)
                    self.cooling.sw.off()
                    delay(1*us)

                    # pumping
                    self.pumping.sw.on()
                    delay(50*us)
                    self.pumping.sw.off()

                    # Trun off all light and wait for delay time to heat ion
                    delay(delay_time*us)

                    # turn on 435 
                    self.ttl_435.off()
                    delay(rabi_time*us)
                    self.ttl_435.on()

                    # meaure count
                    with parallel:
                        self.pmt.gate_rising(300*us)
                        self.cooling.sw.on()
                        photon_number = self.pmt.count(now_mu())
                        photon_count = photon_count + photon_number
                        if photon_number > 1:
                            temp_count = temp_count + 1
                    self.ttl_935_EOM.off()

            data_count[i] = temp_count
            data_aom_frequency[i] = AOM_435


        self.saveData(data_aom_frequency,data_count)

    @rpc(flags = {"async"})
    def saveData(self, xdata, ydata):
        # xdata = np.arange(0,200,1)
        plt.figure()
        plt.plot(xdata, ydata)
        plt.show()
