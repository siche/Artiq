"""
Fix red  and blue sideband detuning 
Vary delay time
Vary rabi time to get the phonon number
"""


import numpy as np
import time, csv
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
    def saveData(self, data):
        # xdata = np.arange(0,200,1)
        # Save the data as csv file
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        csv_name = 'data\\'+"HeatRate3"+"-"+time_now+".csv"

        with open(csv_name,"w",newline='') as t:
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
        # N：the number of rabi_times
        # M: the number of delay times
        N = 100
        M = 21

        delay_times = np.linspace(0,5000,M)
        rabi_times = np.linspace(0,100,N)

        rabi_time = 75.0
        delay_time = 0.0

        _RED_SIDEBAND = 238.139
        _BLUE_SIDEBAND = 241.804
        WL_871 = 871.034655

        # data container
        data = np.zeros((N,3*M+3))

        # the first column is the rabi times
        # the -2 column is the delay times
        # the -1 column is the mean phonon number
        # the inner part are the scan data
        data[:,0] = np.transpose(rabi_times)
        data[:M,-2] = np.transpose(delay_times)

        for m in trange(M):
            delay_time = delay_times[m]

            while not is_871_locked(WL_871):
                print("871 is Out of Lock")
                time.sleep(5)
        
            for n in range(N):
                rabi_time = rabi_times[n]

                # red sideband detection
                DDS.set_frequency(port=0, frequency=_RED_SIDEBAND, amplitude=DDS_AMP,phase=0)
                time.sleep(0.02)
                temp_data1 = self.HeatingRate(DelayTime=delay_time,RabiTime=rabi_time)
                data[n,3*m+1] = temp_data1
                print("Red Sideband Event Count:%s" % temp_data1)

                # blue sideband detection
                DDS.set_frequency(port=0, frequency=_BLUE_SIDEBAND,amplitude=DDS_AMP,phase=0)
                time.sleep(0.02)
                temp_data2 = self.HeatingRate(DelayTime=delay_time, RabiTime=rabi_time)
                data[n,3*m+2] = temp_data2
                print("Blue Sideband Event Count:%s" % temp_data2)

                # calculate mean phono number
                temp_data3 = 0
                if (temp_data1-temp_data2)!=0:
                    temp_data3 = (100-temp_data1)/(temp_data1-temp_data2)
                data[n,3*m+3] = temp_data3
                print("Mean Phonon:%.2f" % temp_data3)

            # average over rabi time
            phonon_numbers = data[:,3*m+3]
            mean_phonon_number = phonon_numbers[phonon_numbers!=0].mean()
            data[m,-1] = mean_phonon_number
    
        self.saveData(data)







