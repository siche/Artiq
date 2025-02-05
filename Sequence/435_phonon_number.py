import sys, os, msvcrt, time
import signal, atexit, win32api, win32con

import numpy as np
from tqdm import trange

from artiq.experiment import *
from save_data import save_file
import matplotlib.pyplot as plt
from wlm_web import wlm_web


from image_processing import has_ion
from ttl_client import shutter
from SMB100B import SMB100B

wm = wlm_web()
wl_871 = 0.0

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

ccd_on = flip_mirror.on
pmt_on = flip_mirror.off
# dds_435 = DDS_AD9910()


def is_871_locked(lock_point=871.034616):
    global wl_871
    wl_871 = wm.get_channel_data(0)
    is_locked = abs(wl_871-lock_point) < 0.000005
    return is_locked


def prog_bar(N):
    widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
               Timer(), ' ', ETA(), ' ']
    pbar = ProgressBar(widgets=widgets, maxval=10*N).start()
    return pbar


def print_info(item):
    print("Accuracy:%.1f%%" % (item[1]))
    print('Photon Count:%d' % item[2])
    print('\n')


def file_write(file_name, content):
    file = open(file_name, 'a')
    file.write(content)
    file.close()

def register_frequency(fre, effi):
    time_now = time.strftime("%Y-%m-%d-%H-%M")
    file = open('data\\long_term_register.csv','a')
    content = time_now + ',' + str(fre) + ',' + str(effi) + '\n'
    file.write(content)
    file.close()

@atexit.register
def closeAll():
    pass


class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')
        self.ttl_935_AOM = self.get_device('ttl4')
        self.ttl_935_EOM = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

    @kernel
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.microwave.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)
        self.microwave.set(400.*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(20.)
        self.cooling.set_att(10.)
        self.microwave.set_att(0.)
        self.pumping.set_att(18.)

    @kernel
    def run_sequence(self, rabi_time, run_times = 100):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        for i in range(run_times):
            with sequential:

                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
                delay(1*us)

                # pumping
                self.pumping.sw.on()
                delay(25*us)
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
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

                # turn on 935 sideband
                self.ttl_935_EOM.off()
                self.cooling.sw.on()

        return (100*count/run_times, photon_count)

    def run(self):
        self.pre_set()

        pmt_on()
        init_fre = 239.68
        sideband_fre1 = 228.38
        carrier_fre = 239.7
        sideband_fre2 = 250.8

        lock_point = 871.034662
        scan_step = 0.001/2

        rabi_time = 200
        scan_times = 200*2
        N = 3*scan_times

        run_times = 200

        file_name = 'data\\Rabi_AOM_fre_Scan'+str(init_fre)+'-'+\
                     str(float(init_fre+N*scan_step))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_fre, init_fre+scan_step*(N-1), N)

        for i in trange(N):

            if i < scan_times:
                init_fre = sideband_fre1
            elif i < scan_times*2:
                init_fre = carrier_fre - scan_times*scan_step
            else: 
                init_fre = sideband_fre2 - 2*scan_times*scan_step

            AOM_435 = init_fre+scan_step*i  # - 0.001*N/2

            # wait for 871 to be locked
            while not is_871_locked(lock_point):
                print('Laser is locking...')
                time.sleep(3)

            # change AOM frequency
            code = "conda activate base && python dds.py " + str(AOM_435)
            os.system(code)

            # run detection and save data
            temp = self.run_sequence(rabi_time, run_times)

            # print information
            data_item = [AOM_435, temp[0], temp[1], wl_871]
            data[:, i] = data_item

            # write data
            content = str(data[0, i])+','+str(data[1, i]) + \
                ','+str(data[2, i])+','+str(data[3, i])+'\n'

            file_write(file_name, content)
            print_info(data_item)
            print('\n')
    
        min_index = data[1,:].argmin(axis=0)
        register_frequency(data[0,min_index],data[1,min_index])

        file.close()
        save_file(data, file_name[5:-4])
                
        # plot figures
        plt.figure(1)
        x1 = data[0,:scan_times]
        y1 = data[1,:scan_times]

        x2 = data[0,scan_times:2*scan_times]
        y2 = data[1,scan_times:2*scan_times]

        x3 = data[0,2*scan_times:]
        y3 = data[1,2*scan_times:]
        
        ax1 = plt.subplot(131)
        ax2 = plt.subplot(132)
        ax3 = plt.subplot(133)

        ax1.plot(x1,y1)
        ax2.plot(x2,y2)
        ax3.plot(x3,y3)
        plt.show()