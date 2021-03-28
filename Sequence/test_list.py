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
    def run_sequence(self,run_times = 100) -> TList(TInt32):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        all_count = [0]*10
        
        for j in range(10):
            rabi_time = 10*j + 1
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
            all_count[j] = count
        return all_count

    def run(self):
        self.pre_set()

        pmt_on()
        AOM_435 = 238.381 
        lock_point = 871.034647
        run_times = 100
        amp = 0.9

        temp = self.run_sequence(run_times)

        print(temp)
        x_time = 10*range(10)
        y_event_count = temp[0]
        y_photon_count = temp[1]
        # plot figures
        plt.figure(1)
       
        plt.plot(x_time, y_event_count)
        plt.show()