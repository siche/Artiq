"""
Fix red  and blue sideband rabi time 
Vary delay time
Vary detuning to get the phonon number
"""

import numpy as np
import time
import csv
from artiq.experiment import *
import matplotlib.pyplot as plt
from dds import *
from tqdm import trange
from wlm_web import wlm_web

wm = wlm_web()

def is_871_locked(lock_point=871.034655):
    global wl_871
    wl_871 = wm.get_channel_data(0)
    is_locked = abs(wl_871-lock_point) < 0.000005
    return is_locked

DDS = dds_controller('COM5')

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

    @kernel
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.dds1_435.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        # self.dds1_435.set(_RED_SIDEBAND*MHz)
        self.pumping.set(260*MHz)

        self.dds1_435.set_att(18.)
        self.cooling.set_att(10.)
        self.pumping.set_att(18.)

        # define dataset
        # self.set_dataset("SBCData", np.full(100, 0), broadcast=True)

    @kernel
    def HeatingRate(self, DelayTime=0.0, RabiTime=20.0):
        # initialize dds
        self.core.break_realtime()
        self.dds1_435.sw.off()
        self.pumping.sw.off()

        event_count = 0
        photon_number = 0

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
                delay(DelayTime*us)

                # turn on 435
                with parallel:
                    self.ttl_435.off()
                    self.ttl_935_AOM.on()
                    self.ttl_935_EOM.on()

                delay(RabiTime*us)
                self.ttl_435.on()

                self.ttl_935_AOM.off()
                # meaure count
                with parallel:
                    self.cooling.sw.on()
                    self.pmt.gate_rising(300*us)
                    photon_number = self.pmt.count(now_mu())
                    if photon_number > 1:
                        event_count = event_count + 1
                self.ttl_935_EOM.off()
                self.cooling.sw.on()
        return event_count

    @rpc(flags={"async"})
    def saveData(self, file_name,data):
        # xdata = np.arange(0,200,1)
        # Save the data as csv file
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        csv_name = 'data\\'+"HeatRate2"+"-"+time_now+".csv"

        with open(file_name, "w", newline='') as t:
            file = csv.writer(t)
            file.writerows(data)

        """
        np.save('xdata.npy', xdata)
        np.save('ydata.npy', ydata)
        plt.figure()
        plt.plot(xdata, ydata)
        plt.show()
        """

    def run(self):
        self.pre_set()

        # heating rate measurement

        # DDS parametr
        DDS_AMP = 0.5
        aom_scan_step = 0.001

        # Scan parametr
        # N：the number of frequency
        # M: the number of delay times
        N = 100
        M = 5

        delay_times = np.linspace(2250, 3500, M)

        rabi_time = 75.0
        delay_time = 0.0

        _RED_SIDEBAND = 238.142
        _BLUE_SIDEBAND = 241.804
        WL_871 = 871.034655

        aom_scan_steps = np.arange(0, N*aom_scan_step, aom_scan_step)
        _RED_SIDEBANDS = _RED_SIDEBAND - N/2*aom_scan_step+aom_scan_steps
        _BLUE_SIDEBANDS = _BLUE_SIDEBAND - N/2*aom_scan_step + aom_scan_steps

        # data container
        # the first column is the redetunings
        # the -2 column is the delaytimes

        data = np.zeros((N, 2*M+4))
        data[:, 0] = np.transpose(_RED_SIDEBANDS)
        data[:, 1] = np.transpose(_BLUE_SIDEBANDS)
        data[:M,-2] = np.transpose(delay_times)

        AOM_435 = 0.0

        # define filename
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        csv_name = 'data\\'+"HeatRate2"+"-"+time_now+".csv"

        for m in trange(M):
            delay_time = delay_times[m]
            while not is_871_locked(WL_871):
                print("871 is Out of Lock")
                time.sleep(5)
        
            for n in range(N):

                # blue sideband
                AOM_435 = _RED_SIDEBANDS[n]
                DDS.set_frequency(port=0, frequency=AOM_435,
                                  amplitude=DDS_AMP, phase=0)
                time.sleep(0.02)
                temp_data1 = self.HeatingRate(
                    DelayTime=delay_time, RabiTime=rabi_time)
                data[n,2*m+2] = temp_data1
                print("Event Count:%s" % temp_data1)

                # blue sidebands
                AOM_435 = _BLUE_SIDEBANDS[n]
                DDS.set_frequency(port=0, frequency=AOM_435,
                                  amplitude=DDS_AMP, phase=0)
                time.sleep(0.02)
                time.sleep(0.02)
                temp_data2 = self.HeatingRate(DelayTime=delay_time, RabiTime=rabi_time)
                data[n,2*m+3] = temp_data2

                print("Event Count:%s" % temp_data2)

            # try to calculate the phonon number
            red_data = data[:,2*m+2].min()
            blue_data = data[:,2*m+3].min()
            
            phonon_number = -1
            if red_data*blue_data!=0:
                phonon_number = (100-red_data)/(red_data-blue_data)
            data[m,-1] = phonon_number
            np.save('data.npy',data)
        # combine data
        self.saveData(data)
