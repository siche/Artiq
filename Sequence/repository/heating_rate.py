import numpy as np
import time
from artiq.experiment import *
import matplotlib.pyplot as plt

_RED_SIDEBAND = 238.146-0.001*50
_BLUE_SIDEBAND = 241.103

class HeatingRateMeasurement(EnvExperiment):
    def build(self):

        # define HardWare device
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]

        self.setattr_device('core')
        self.dds1_435 = self.get_device(dds_channel[2])
        self.cooling = self.get_device(dds_channel[1])
        self.pumping = self.get_device(dds_channel[3])

        self.pmt = self.get_device('ttl0')
        self.ttl_935_AOM = self.get_device('ttl4')
        self.ttl_935_EOM = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

    def run(self):
        t1 = time.time()
        self.pre_set()
        self.HeatingRate()
        t2 = time.time()
        print("time cost:%s" % (t2-t1))

    @kernel
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.dds1_435.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.dds1_435.set(_RED_SIDEBAND*MHz)
        self.pumping.set(260*MHz)

        self.dds1_435.set_att(18.)
        self.cooling.set_att(10.)
        self.pumping.set_att(18.)

        # define dataset
        # self.set_dataset("SBCData", np.full(100, 0), broadcast=True)

    @kernel
    def HeatingRate(self,delay_time=1, rabi_time = 20):
        # initialize dds
        self.core.break_realtime()
        self.dds1_435.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0

        aom_scan_step = 0.001
        temp_count = 0
        N = 100

        data_aom_frequency = [0.0]*100
        data_count = [0]*100
        AOM_435 =238.146

        for i in range(10):
            
            
            # set 435 aom frequency  
            AOM_435 = _RED_SIDEBAND + float(i)*aom_scan_step
            # self.core.break_realtime()

            delay(80*us)
            self.dds1_435.set(AOM_435*MHz)
            # delay(26*ms)
            
            temp_count = 0
            
            # 对于每一个frequency测量100次
            for j in range(100):
                with sequential:

                    # 0.0 doppler cooling
                    self.cooling.sw.on()
                    delay(1*ms)
                    self.cooling.sw.off()
                    delay(1*us)

                    # pumping
                    self.pumping.sw.on()
                    delay(30*us)
                    self.pumping.sw.off()

                    # Trun off all light and wait for delay time to heat ion
                    delay(delay_time*us)

                    # turn on 435 
                    with parallel:
                        self.ttl_435.off()
                        self.ttl_935_EOM.on()

                    delay(rabi_time*us)
                    self.ttl_435.on()

                    # meaure count
                    with parallel:
                        self.cooling.sw.on()
                        self.pmt.gate_rising(300*us)
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
        np.save('xdata.npy',xdata)
        np.save('ydata.npy',ydata)
        plt.figure()
        plt.plot(xdata, ydata)
        plt.show()
