
from wlm_lock import laser_lock

import sys
import os
import select
import numpy as np
from artiq.experiment import *

from save_data import save_file
from wlm_web import wlm_web
import time

from image_processing import has_ion
from ttl_client import shutter

from wlm_web import wlm_web

if os.name == "nt":
    import msvcrt

laser_lock_370 = laser_lock(port=6791)
shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

ccd_on = flip_mirror.off
pmt_on = flip_mirror.on
wm = wlm_web()

def file_write(file_name, content):
    file = open(file_name, 'a')
    file.write(content)
    file.close()

def is_locked(des_fre):
    state = abs(wm.get_wavelengths()[1] - des_fre) < 3/1000000
    return state

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')
        self.ttl_935 = self.get_device('ttl7')
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
        self.cooling.set_att(19.)
        self.microwave.set_att(0.)
        self.pumping.set_att(25.)

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
        for i in range(1000):
            with sequential:

                self.detection.sw.off()

                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(1.5*ms)
                self.cooling.sw.off()
                delay(1*us)

                # detection on
                with parallel:
                    # self.detection.sw.on()
                    self.detection.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

        self.cooling.sw.on()
        self.detection.sw.off()

        return (count, photon_count)

    def run(self):

        self.pre_set()
        pmt_on()

        center_370_wavelength = 369.526100
        laser_scan_step = -0.000001
        N = 60

        init_370_wavelength = center_370_wavelength - laser_scan_step*N/2
        data = np.zeros((3,N))
        
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        file_name = 'data\\'+str(init_370_wavelength)+'-'+str(init_370_wavelength+N*laser_scan_step)+'-'+time_now+'.csv'
        file = open(file_name, 'w+')
        file.close()

        for i in range(N):
            wavelength_370 = init_370_wavelength + i*laser_scan_step
            laser_lock_370.lock(wavelength_370)
            laser_lock_370.lock_on()
            while not is_locked(wavelength_370):
                time.sleep(5)
                print('wait for 370 to be locked')

            temp = self.run_sequence()
            data[:,i] = [wavelength_370, temp[0], temp[1]]

            content = str(wavelength_370) + ',' + \
                      str(temp[0]) + ',' + str(temp[1])+'\n'
            file_write(file_name, content)

            print('Count:%d\nEffiency:%.1f%%' %(temp[1], temp[0]))
        file.close()
        save_file(data, __file__[:-3])

        laser_lock_370.lock(369.526100)
        laser_lock_370.lock_on()
        while not is_locked(369.526100):
            time.sleep(2)
            print('Set back to initial frequency')