import numpy as np
import time
from artiq.experiment import *
import matplotlib.pyplot as plt

_RED_SIDEBAND = 238.142
_CARRIER = 238.142

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

        self.dds1_435.set_att(18.)
        self.cooling.set_att(10.)
        self.pumping.set_att(18.)

        # define dataset
        # self.set_dataset("SBCData", np.full(100, 0), broadcast=True)
    @kernel
    def SingleRun(self, rabi_time, run_times=200):
        # initialize dds
        self.core.break_realtime()
        # self.microwave.sw.off()
        self.pumping.sw.off()

        # photon_count = 0
        photon_number = 0
        count = 0

        with sequential:
            self.cooling.sw.on()
            delay(1*ms)
            self.cooling.sw.off()
            delay(1*us)

        for i in range(run_times):
            # with sequential:

            # cooling for 1.5 ms
            """
            self.cooling.sw.on()
            delay(1*ms)
            self.cooling.sw.off()
            delay(1*us)
            """

            # pumping
            self.pumping.sw.on()
            delay(50*us)
            self.pumping.sw.off()
            delay(1*us)

            # turn on 435 and turn off 935 sideband
            # with parallel:
            # turn off 935 sideband

            # turn off 935
            # turn off 935 sideband
            self.ttl_935_EOM.on()
            self.ttl_935_AOM.on()
            delay(1*us)

            # turn on 435
            self.ttl_435.off()
            delay(rabi_time*us)
            self.ttl_435.on()
            delay(1*us)

            # microwave on
            """
                self.microwave.sw.on()
                delay(26.1778*us)
                self.microwave.sw.off()
                """
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
        return count

    @kernel
    def RabiTimeScan(self, start=239.0, stop=240.0, step=1.0, run_times=100):
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

                # turn on 435 and turn off 935 sideband
                # with parallel:
                # turn off 935 sideband

                # turn off 935
                # turn off 935 sideband
                self.ttl_935_EOM.on()
                self.ttl_935_AOM.on()
                delay(1*us)

                # turn on 435
                self.ttl_435.off()
                delay(rabi_time*us)
                self.ttl_435.on()
                delay(1*us)

                # microwave on
                """
                    self.microwave.sw.on()
                    delay(26.1778*us)
                    self.microwave.sw.off()
                    """
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

            all_count[j] = count
            all_time[j] = rabi_time
        self.AnalysisData(all_count, all_time)

    @rpc(flags={"async"})
    def AnalysisData(self, ydata1, ydata2):
        xdata = np.arange(self.start, self.stop, self.step)
        plt.figure()
        plt.plot(xdata, ydata1)
        print(ydata2)
        plt.show()

    def run(self):
        t1 = time.time()
        self.start = 0.0
        self.stop = 200.0
        self.step = 2.0

        self.pre_set()
        self.RabiTimeScan(self.start, self.stop, self.step)
        # self.RabiTimeScan(self.start, self.stop, self.step, run_times=100)
        t2 = time.time()
        print("running time cost:%s" % (t2-t1))
