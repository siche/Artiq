import numpy as np
import time
import csv
from artiq.experiment import *
import matplotlib.pyplot as plt
from dds2 import *

_CARRIER = 241.893
_CARRIER_AMP = 0.8

"""
DDS = dds_controller("COM5")    
DDS.set_frequency(frequency=_CARRIER, amplitude=AMP)
"""


def saveData(data):
    # xdata = np.arange(0,200,1)
    # Save the data as csv file
    time_now = time.strftime("%Y-%m-%d-%H-%M")
    csv_name = 'data\\'+"RabiTime"+"-"+time_now+".csv"

    with open(csv_name, "w", newline='') as t:
        file = csv.writer(t)
        file.writerows(data)


class FrequencyScan(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')

        # DDS port
        self.dds935 = self.get_device(dds_channel[0])
        self.light = self.get_device(dds_channel[1])
        self.dds435 = self.get_device(dds_channel[2])

        # Rf switch
        self.pmt = self.get_device('ttl0')
        self.coolingSwitch = self.get_device('ttl4')
        self.repumpingSwitch = self.get_device('ttl5')
        self.pumpingSwitch = self.get_device('ttl6')
        self.rabiSwitch = self.get_device('ttl7')

    @kernel
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.dds1_435.init()
        self.pumping.init()

        # profile 0: cooling
        self.cooling.set(250*MHz, profile=0)
        self.cooling.cpld.set_profile(0)

        # 435 dds profile
        self.dds1_435.set(frequency=_CARRIER*MHz)

        # pumping
        self.pumping.set(260*MHz)

        # set attenuator
        self.dds1_435.set_att(18.)
        self.cooling.set_att(20.)
        self.pumping.set_att(18.)

        # define dataset
        # self.set_dataset("SBCData", np.full(100, 0), broadcast=True)
    @kernel
    def SingleRun(self, AOM_fre=240.0, rabi_time=100.0, run_times=200):

        # initialize dds
        self.core.break_realtime()
        self.light.cpld.set_profile(0)
        delay(2*us)

        with parallel:
            self.light.sw.on()
            self.dds935.sw.on()
        delay(2*us)

        with parallel:
            self.coolingSwitch.on()
            self.pumpingSwitch.off()
            self.repumpingSwitch.on()

        delay(20*us)
        self.dds435.set(AOM_fre)
        delay(10*us)

        photon_count = 0
        photon_number = 0
        count = 0

       

        for i in range(run_times):
            # Doppler Cooling
            with sequential:

                # cooling for 1.5 ms
                self.light.sw.on()
                delay(2.0*ms)

                # pumping
                self.light.cpld.set_profile(1)
                delay(2*us)

                with parallel:
                    self.coolingSwitch.off()
                    self.pumpingSwitch.on()

                delay(5*us)

                # turn off 370
                # turn off pumping EOM
                # turn off 935
                # turn off 935 EOM

                with parallel:
                    self.light.sw.off()
                    self.pumpingSwitch.off()
                    self.dds935.sw.off()
                    self.repumpingSwitch.off()

                delay(2*us)

                # turn on 435
                self.rabiSwitch.on()
                delay(rabi_time*us)
                self.rabiSwitch.off()

                # detection on
                # turn on 370
                # turn cooling EOM
                # turn on 935
                # turn off 935 EOM
                with parallel:

                    self.light.sw.on()
                    self.dds935.sw.on()
                    self.coolingSwitch.on()

                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

                with parallel:
                    self.light.cpld.set_profile(0)
                    self.coolingSwitch.on()
                    self.repumpingSwitch.on()                
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
        rabi_time = 100.0

        start_fre = 241.8
        stop_fre = 242.1
        fre_step = 0.001
        N = int((stop_fre-start_fre)/fre_step)

        data = np.zeros((N, 2))
        xdata = start_fre + fre_step*np.arange(N)
        ydata = [None]*N

        plt.ion()
        fig, = plt.plot(xdata, ydata)
        ax = plt.gca()

        for i in range(N):
            aom_fre = xdata[i]
            count = self.SingleRun(
                AOM_fre=aom_fre, rabi_time=rabi_time, run_times=200)
            ydata[i] = count
            data[i, 0] = aom_fre
            data[i, 1] = count

            ax.relim()
            ax.autoscale_view(True, True, True)
            fig.set_ydata(ydata)
            plt.pause(1e-17)
            plt.draw()

        t2 = time.time()
        print("running time cost:%s" % (t2-t1))

        plt.draw()

        time_now = time.strftime("%Y-%m-%d-%H-%M")
        csv_name = 'data\\'+"RabiFreScan"+"-" + \
            str(start_fre)+'-'+str(stop_fre)+'-'+time_now+".csv"

        with open(csv_name, "w", newline='') as t:
            file = csv.writer(t)
            file.writerows(data)
