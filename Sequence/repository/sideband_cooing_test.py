import numpy as np
import time
from artiq.experiment import *
import matplotlib.pyplot as plt
from dds2 import *

_RED_SIDEBANDS = [234.412,234.735]
_CARRIER = 236.267
AMP = 0.600

"""
DDS = dds_controller("COM5")
DDS.set_frequency(frequency=_CARRIER, amplitude=AMP)
"""


class SideBandCooling(EnvExperiment):
    def build(self):

        # define HardWare device
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        # self.dds1_435 = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.dds1_435 = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])

        self.pmt = self.get_device('ttl0')
        self.ttl_935_AOM = self.get_device('ttl4')
        self.ttl_935_EOM = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

    @kernel
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.dds1_435.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.dds1_435.set(_CARRIER*MHz)
        self.pumping.set(260*MHz)

        self.dds1_435.set_att(20.)
        self.cooling.set_att(10.)
        self.pumping.set_att(18.)

        # define dataset
        # self.set_dataset("SBCData", np.full(100, 0), broadcast=True)
    @kernel
    def SingleRun(self, rabi_time=20.0, run_times=200):

        self.core.break_realtime()

        count = 0
        photon_number = 0

        for i in range(run_times):
            # with sequential:
            self.cooling.sw.on()
            delay(1*ms)
            self.cooling.sw.off()
            delay(1*us)
            # cooling for 1.5 ms
            # pumping
            self.pumping.sw.on()
            delay(50*us)
            self.pumping.sw.off()
            delay(1*us)

            # sideband cooling
            for i in range(2):
                self.dds1_435.set(_RED_SIDEBANDS[i]*MHz)
                delay(20*us)

                for i in range(5):
                    with parallel:
                        self.ttl_935_AOM.on()
                        self.ttl_935_EOM.on()
                        self.ttl_435.off()

                    delay(500*ms)
                    self.ttl_435.on()
                    delay(1*us)

                        # 1.2 Pumping Back
                    self.ttl_935_AOM.off()
                    self.ttl_935_EOM.off()
                    delay(100*us)

                    self.pumping.sw.on()
                    delay(40*us)
                    self.pumping.sw.off()
                    delay(1*us)
            
            # turn on 435 and turn off 935 sideband
            # with parallel:
            # turn off 935 sideband

            # turn off 935
            # turn off 935 sideband
            self.dds1_435.set(_CARRIER*MHz)
            delay(100*us)
    
            self.ttl_935_EOM.on()
            self.ttl_935_AOM.on()
            delay(1*us)

            # turn on 435
            self.ttl_435.off()
            delay(rabi_time*us)
            self.ttl_435.on()
            delay(1*us)

            # detection
            # turn on 935 without sideband
            self.ttl_935_AOM.off()

            # detection on
            with parallel:
                # self.detection.sw.on()
                # 利用cooling  光作为detection
                self.pmt.gate_rising(300*us)
                self.cooling.sw.on()
                photon_number = self.pmt.count(now_mu())
                # photon_count = photon_count + photon_number
                if photon_number > 1:
                    count = count + 1

            # turn on 935 sideband
            self.ttl_935_EOM.off()
            self.cooling.sw.on()
        return(count)

    @kernel
    def RabiTimeScan(self, start=239.0, stop=240.0, step=1.0, run_times=100):

        _RED_SIDEBANDS = [238.140, 238.346, 238.431]
        _CARRIER = 239.955
        # initialize dds
        self.core.break_realtime()
        self.pumping.sw.off()

        N = int((stop-start)/step)
        # N = 100
        all_count = [0]*N
        all_time = [0.0]*N
        rabi_time = 0.0

        for j in range(N):
            rabi_time = start + step*j
            count = 0
            photon_number = 0

            self.cooling.sw.on()
            delay(1*ms)
            self.cooling.sw.off()
            delay(1*us)

            for i in range(run_times):
                # with sequential:
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
                delay(1*us)
                # cooling for 1.5 ms
                # pumping
                self.pumping.sw.on()
                delay(50*us)
                self.pumping.sw.off()
                delay(1*us)

                # sideband cooling
                for i in range(3):
                    self.dds1_435.set(_RED_SIDEBANDS[i]*MHz)
                    delay(1*ms)
                    for i in range(10):
                        with parallel:

                            # 1.1 turn off 935 sideband
                            self.ttl_935_AOM.on()
                            self.ttl_935_EOM.on()
                            self.ttl_435.off()
                        delay(50*us)

                        self.ttl_435.on()

                        # 1.2 Pumping Back
                        self.ttl_935_AOM.off()
                        self.ttl_935_EOM.off()
                        delay(100*us)

                        self.pumping.sw.on()
                        delay(40*us)
                        self.pumping.sw.off()
                # turn on 435 and turn off 935 sideband
                # with parallel:
                # turn off 935 sideband

                # turn off 935
                # turn off 935 sideband
                self.dds1_435.set(_CARRIER*MHz)
                delay(100*us)

                self.ttl_935_EOM.on()
                self.ttl_935_AOM.on()
                delay(1*us)

                # turn on 435
                self.ttl_435.off()
                delay(rabi_time*us)
                self.ttl_435.on()
                delay(1*us)

                # detection
                # turn on 935 without sideband
                self.ttl_935_AOM.off()

                # detection on
                with parallel:
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.pmt.gate_rising(300*us)
                    self.cooling.sw.on()
                    photon_number = self.pmt.count(now_mu())
                    # photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

                # turn on 935 sideband
                self.ttl_935_EOM.off()
                self.cooling.sw.on()
        self.AnalysisData(all_count, all_time)

    @rpc(flags={"async"})
    def AnalysisData(self, ydata1, ydata2):
        xdata = np.arange(self.start, self.stop, self.step)
        plt.figure()
        plt.plot(xdata, ydata1)
        print(ydata2)
        plt.show()

    def run(self):
        
        self.pre_set()
        time.sleep(0.1)
        t1 = time.time()
        N = 100
        step = 0.5
        rabi_time = 0.0
        all_count = [None]*N
        xdata = np.arange(N)

        plt.ion()
        fig, = plt.plot(xdata,all_count)
        ax = plt.gca()

        for i in range(N):
            rabi_time = rabi_time+step
            count = self.SingleRun(rabi_time=rabi_time)
            all_count[i] = count
            print("Evevnt Count:%d" % count)
            ax.relim()
            ax.autoscale_view(True, True, True)
            fig.set_ydata(all_count)
            plt.draw()
            plt.pause(1e-17)
        t2 = time.time()
        print("running time cost:%s" % (t2-t1))
        plt.show()
        # plot figure