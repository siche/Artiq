import sys, os, time

import numpy as np
from artiq.experiment import *
from save_data import save_file
from progressbar import *
import matplotlib.pyplot as plt
from wlm_web import wlm_web

from wlm_lock import laser_lock
from image_processing import has_ion
from ttl_client import shutter
from current_client import current_web
# from load_ion_client import reload_ion

if os.name == "nt":
    import msvcrt

wm = wlm_web()
curr = current_web()
laser_871_lock = laser_lock()

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

ccd_on = flip_mirror.off
pmt_on = flip_mirror.on


def reload_ion():
    t1 = time.time()
    print('RELOADING...')
    pmt_on()
    time.sleep(0.3)
    ccd_on()
    time.sleep(1)
    # is_there_ion = has_ion()
    costed_time = 0
    while (not has_ion()==1 and costed_time < 900):
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
    time.sleep(0.1)

def is_871_locked(lock_point=344.179696):
    fre_871 = wm.get_frequencies()[0]

    # if frequency gap is within +-3MHz then locked
    is_locked = abs(fre_871-lock_point) < 3/10**6
    # print('gap is:%.6f' % (fre_871-lock_point))
    return is_locked


def prog_bar(N):
    widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
               Timer(), ' ', ETA(), ' ']
    pbar = ProgressBar(widgets=widgets, maxval=10*N).start()
    return pbar

def file_write(file_name, content):
    file = open(file_name, 'a')
    file.write(content)
    file.close()


def get_data(file_name, aom_scan_step=50/1e3):
    file = open(file_name, 'r')
    file.seek(0)
    item = file.readline()
    rescan_points = []

    while item:
        data = item[:-1].split(',')
        temp_fre = float(data[0])
        temp_lock = float(data[-1])

        for i in range(-5, 6):
            fre1 = round(temp_fre+i*aom_scan_step, 2)
            rescan_points.append((fre1, temp_lock))
        item = file.readline()

    unique_rescan_points = []

    for point in rescan_points:
        if point not in unique_rescan_points:
            unique_rescan_points.append(point)

    file.close()
    unique_rescan_points.sort(key=lambda x: x[1])
    return unique_rescan_points


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
        for i in range(100):
            with sequential:
                # turn off 435
                self.ttl_435.on()
                self.ttl_935.off()
                self.detection.sw.off()

                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(1.5*ms)
                self.cooling.sw.off()
                delay(1*us)

                # pumping
                self.pumping.sw.on()
                delay(50*us)
                self.pumping.sw.off()
                delay(1*us)

                # turn on 435 and turn off 935 sideband
                # with parallel:
                # turn off 935
                self.ttl_935.on()
                delay(1*us)

                # turn on 435
                self.ttl_435.off()
                delay(1000*us)
                self.ttl_435.on()
                delay(1*us)

                # microwave on
                # self.microwave.sw.on()
                # delay(80*us)
                # self.microwave.sw.off()

                # detection on
                with parallel:
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.cooling.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

                # turn on 935
                self.ttl_935.off()
                self.detection.sw.off()

        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()

        # turn on 935
        self.ttl_935.off()
        # self.ttl_435.on()
        return (count, photon_count)

    def run(self):
        self.pre_set()

        pmt_on()

        # aom frequnecy is interms of MHz
        aom_scan_step = 10/1000  # 50kHz
        rescan_file = 'data\\manual-rescan-344179220.0-344178920.0-2019-12-12-20-10.csv'
        rescan_data = get_data(rescan_file, aom_scan_step)

        N = len(rescan_data)
        widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
                   Timer(), ' ', ETA(), ' ']
        pbar = ProgressBar(widgets=widgets, maxval=10*N).start()

        # save file
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        file_name = 'data\\auto-rescan'+'-'+time_now+'.csv'
        file = open(file_name, 'w+')
        file.close()

        # save data
        data = np.zeros((4, N))

        for i in range(N):
            fre_871 = rescan_data[i][1]
            AOM_435 = rescan_data[i][0]

            # convert MHz in to THz
            laser_871_lock.lock(fre_871/10**6)
            laser_871_lock.lock_on()

            # wait for 871 to be locked
            while not is_871_locked(fre_871/10**6):
                print('wait for 871 to be locked ...')
                time.sleep(1)

            # change AOM frequency
            code = "conda activate base && python dds.py " + str(AOM_435)
            os.system(code)

            # run detection and save data
            temp = self.run_sequence()

            # judge if there is only one ion
            # if there is more than one turn off RF and reload ion
            if temp[1] < 90 and not has_ion==1:
                reload_ion()
                temp = self.run_sequence()
            # print information
            data_item = [AOM_435, fre_871, temp[0], temp[1]]
            data[:, i] = data_item

            # write data
            content = str(data[0, i])+','+str(data[3, i])+\
                ',' + str(data[2, i])+','+str(data[1, i])+'\n'
            file_write(file_name, content)


            print('Count:%d' % temp[1])
            print('Effiency:%.1f%%' % temp[0])
            pbar.update(10*i+1)
            print('\n')

        file.close()
       