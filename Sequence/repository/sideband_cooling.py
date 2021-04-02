import numpy as np
import time
from artiq.experiment import *
import matplotlib.pyplot as plt

_RED_SIDEBAND = 238.103

class SideBandCooling(EnvExperiment):
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
    def sidebandcooling(self):
        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        N = 100
        all_count = [0]*N
        all_time = [0]*N
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
            delay(1*us)

            # sideband cooling
            # 1. turn off 935 sideband and turn on 435 for
            #    some cooling time
            for i in range(1000):
                with parallel:

                    # 1.1 turn off 935 sideband
                    self.ttl_935_EOM.on()

                    # 1.1 (in the same time) turn on 435
                    # TODO:DDS profile 的切换
                    # self.switch_to_red()
                    self.ttl_435.off()
                delay(50*us)

                self.ttl_435.on()
                # 1.2 Pumping Back
                self.ttl_935_EOM.off()

                self.pumping.sw.on()
                delay(20*us)
                self.pumping.sw.off()

            # delay(*us)
            # 3 cooling result detection
            # Mainly detect the red sideband
            
            for i in range(N):
                scan_time = 2*i
                count = 0
                for j in range(50):
                    with sequential:
                        
                        """
                        self.cooling.sw.on()
                        delay(1000*us)
                        self.cooling.sw.off()
                        delay(1*us)
                        """

                        self.cooling.sw.off()
                        self.pumping.sw.on()
                        delay(50*us)
                        self.pumping.sw.off()
                        delay(1*us)

                        self.ttl_935_EOM.on()
                        self.ttl_935_AOM.on()
                        delay(1*us)

                        self.ttl_435.off()
                        delay(scan_time*us)
                        self.ttl_435.on()
                        delay(1*us)

                        self.ttl_935_AOM.off()

                    with parallel:
                        self.pmt.gate_rising(300*us)
                        self.cooling.sw.on()
                        photon_number = self.pmt.count(now_mu())
                        photon_count = photon_count + photon_number
                        if photon_number > 1:
                            count = count + 1
                    self.ttl_935_EOM.off()
                all_count[i] = count*2
                all_time[i] = scan_time
                #self.mutate_dataset("SBCData", i, count)
            self.saveData(all_time, all_count)

    @rpc(flags = {"async"})
    def saveData(self, xdata, ydata):
        # xdata = np.arange(0,200,1)
        plt.figure()
        plt.plot(xdata, ydata)
        plt.show()
