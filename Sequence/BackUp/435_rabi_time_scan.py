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

from wlm_lock import laser_lock
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
    time.sleep(0.7)


def is_871_locked(lock_point=871.034924):
    wl_871 = wm.get_data()[0]
    is_locked = abs(wl_871-lock_point) < 0.000004
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
    def run_sequence(self, rabi_time, run_times):
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
                # turn off 435
                self.ttl_435.on()
                self.ttl_935.off()
                self.detection.sw.off()

                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(20*ms)
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
                delay(rabi_time*us)
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
        return (100*count/run_times, photon_count)

    def run(self):
        self.pre_set()
        pmt_on()
        AOM_435 = 240.99
        lock_point = 871.035134
        N = 200 
        rabi_time = 0
        rabi_time_step = 5
        run_times = 50

        widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
                   Timer(), ' ', ETA(), ' ']
        pbar = ProgressBar(widgets=widgets, maxval=10*N).start()

        # save file
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        file_name = 'data\\435-rabi-scan'+'-'+time_now+'.csv'
        file = open(file_name, 'w+')
        file.close()

        # save data
        data = np.zeros((4, N))
        code = "conda activate base && python dds.py " + \
            str(AOM_435)
        os.system(code)
        shutter_370.off()
        """
        x_data = list(range(100))
        y_data1 = [None]*100
        y_data2 = [None]*100
        """

        """
        plt.figure(1)
        fig1 = plt.subplot(211)
        line1, = fig1.plot(x_data,y_data1)
        show_data1 = 'Effiency:0'
        txt1 = fig1.text(0.8,0.8,show_data1 ,verticalalignment = 'center', \
                                            transform=fig1.transAxes)

        fig2 = plt.subplot(212)
        line2, = fig2.plot(x_data,y_data2)
        show_data2 = 'Count:0'
        txt2 = fig2.text(0.8,0.8,show_data2,verticalalignment = 'center', \
                                            transform=fig2.transAxes)
        """
        for i in range(N):

            # wait for 871 to be locked
            while not is_871_locked(lock_point):
                print('wait for 871 to be locked ...')
                time.sleep(1)

            # change AOM frequency

            # run detection and save data
            temp = self.run_sequence(rabi_time, run_times)

            # judge if has ion
            if temp[0] < 70 :
                ccd_on()
                time.sleep(0.7)
                if not has_ion():
                    reload_ion()
                    temp = self.run_sequence(rabi_time, run_times)
                else:
                    pmt_on()
                    time.sleep(0.5)
                
            # print information
            data_item = [AOM_435, rabi_time, temp[1], temp[0]]
            data[:, i] = data_item

            # write data
            content = str(data[0, i])+','+str(data[1, i]) +\
                ',' + str(data[2, i])+','+str(data[3, i])+'\n'
            file_write(file_name, content)

            print('Count:%d' % temp[1])
            print('Effiency:%.1f%%' % temp[0])
            pbar.update(10*i+1)
            print('\n')
            rabi_time = rabi_time + rabi_time_step

        file.close()
