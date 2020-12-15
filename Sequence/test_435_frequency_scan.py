import sys
import os
import select
import numpy as np
from artiq.experiment import *
from scipy.optimize import curve_fit
from save_data import save_file
from progressbar import *
import matplotlib.pyplot as plt
from wlm_web import wlm_web
import time

from image_processing import has_ion
from ttl_client import shutter
from current_client import current_web
# from load_ion_client import reload_ion

if os.name == "nt":
    import msvcrt

wm = wlm_web()
curr = current_web()

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

ccd_on = flip_mirror.on
pmt_on = flip_mirror.off


def reload_ion():
    t1 = time.time()
    print('RELOADING...')
    """
    pmt_on()
    time.sleep(0.3)
    ccd_on()
    time.sleep(1)
    """
    # is_there_ion = has_ion()
    costed_time = 0
    while (not has_ion() and costed_time < 900):
        # if not curr.is_on:
        curr.on()
        shutter_370.on()
        shutter_399.on()
        costed_time = time.time()-t1
        print('COSTED TIME:%.1fs' % (costed_time))
        time.sleep(2)

    pmt_on()
    curr.off()
    shutter_370.off()
    shutter_399.off()
    curr.beep()


def fit_func(x, a, b, c, d):
    return a*np.sin(b*x+c)+d


def is_871_locked(lock_point=871.034694):
    wl_871 = wm.get_data()[0]
    is_locked = abs(wl_871-lock_point) < 0.000004
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

        self.detection.set_att(19.4)
        self.cooling.set_att(10.)
        self.microwave.set_att(0.)
        self.pumping.set_att(18.)

    @kernel
    def run_sequence(self):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        for i in range(100):
            with sequential:
                # turn off 435
                self.ttl_435.on()
                self.ttl_935_EOM.off()
                self.detection.sw.off()

                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(400*us)
                self.cooling.sw.off()
                delay(1*us)

                # pumping
                self.pumping.sw.on()
                delay(35*us)
                self.pumping.sw.off()
                delay(1*us)

                # turn on 435 and turn off 935 sideband
                # with parallel:
                # turn off 935 sideband
                # self.ttl_935_EOM.on()
                # delay(1*us)

                # microwave on
                self.microwave.sw.on()
                delay(21.35*us)
                self.microwave.sw.off()
                
                # turn off 935 sideband
                self.ttl_935_EOM.on()

                # turn off 935 sideband
                # self.ttl_935_EOM.on()

                # detection on
                with parallel:
                    # self.detection.sw.on()
                    self.pmt.gate_rising(800*us)
                    self.cooling.sw.on()
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

                # turn on 935 sideband
                self.ttl_935_AOM.off()
                self.ttl_935_EOM.off()
                self.detection.sw.off()

        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()

        # turn on 935
        self.ttl_935_EOM.off()
        # self.ttl_435.on()
        return (count, photon_count)

    def run(self):
        self.pre_set()
        
        N = 100
        for i in range(N):
            # run detection and save data
            temp = self.run_sequence()
            print('%d/%d\t count:%d\t eff:%d%%' % (i+1, N, temp[1], temp[0]))