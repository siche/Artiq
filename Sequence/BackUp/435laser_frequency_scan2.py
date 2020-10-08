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
    while (not has_ion() and costed_time < 900):
        # if not curr.is_on:
        curr.on()
        shutter_370.on()
        shutter_399.on()
        costed_time = time.time()-t1
        print('COSTED TIME:%.1fs' % (costed_time))
        time.sleep(2)

    ccd_on()
    curr.off()
    shutter_370.off()
    shutter_399.off()
    curr.beep()


def fit_func(x, a, b, c, d):
    return a*np.sin(b*x+c)+d


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


def print_info(item):
    print("Accuracy:%.1f%%" % (item[1]))
    print('Photon Count:%d' % item[2])
    print('\n')


def file_write(file_name, content):
    file = open(file_name, 'a')
    file.write(content)
    file.close()


def create_file(min_fre, max_fre):
    file_name = 'data\\'+str(min_fre)+'-'+str(max_fre)+'.csv'
    file = open(file_name, 'w+')
    file.close()

    rescan_file_name = 'data\\rescan-'+str(min_fre)+'-'+str(max_fre)+'.csv'
    rescan_file = open(rescan_file_name, 'w+')
    rescan_file.close()

    manual_rescan_file_name = 'data\\manual-rescan-' + \
        str(min_fre)+'-'+str(max_fre)+'.csv'
    manual_rescan_file = open(manual_rescan_file_name, 'w+')
    manual_rescan_file.close()


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
                delay(500*us)
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
        init_aom_fre = 210
        stop_aom_fre = 240
        aom_scan_step = 50/1000  # 50kHz
        aom_N = int((stop_aom_fre - init_aom_fre)/aom_scan_step)

        # laser_frequency is interms of MHz
        laser_scan_step = -(stop_aom_fre - init_aom_fre)
        init_laser_fre = 344.179520*10**6
    
        laser_N = 2
        N = laser_N*aom_N

        # calculate min and max frequency
        min_fre = init_laser_fre-2*240
        max_fre = init_laser_fre-2*240 + laser_N*laser_scan_step

        # progressbar
        widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
                   Timer(), ' ', ETA(), ' ']
        pbar = ProgressBar(widgets=widgets, maxval=10*N).start()

        # save file
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        file_name = 'data\\'+str(min_fre)+'-'+str(max_fre)+'-'+time_now+'.csv'
        file = open(file_name, 'w+')
        file.close()

        rescan_file_name = 'data\\rescan-'+str(min_fre)+'-'+str(max_fre)+'-'+time_now+'.csv'
        rescan_file = open(rescan_file_name, 'w+')
        rescan_file.close()

        manual_rescan_file_name = 'data\\manual-rescan-' + \
            str(min_fre)+'-'+str(max_fre)+'-'+time_now+'.csv'
        manual_rescan_file = open(manual_rescan_file_name, 'w+')
        manual_rescan_file.close()

        # save data
        data = np.zeros((4, N))
        data[0, :] = np.linspace(min_fre, max_fre, N)

        x_data = list(range(100))
        y_data1 = [None]*100
        y_data2 = [None]*100

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
        for i in range(laser_N):
            fre_871 = init_laser_fre + i*laser_scan_step

            # convert MHz in to THz
            laser_871_lock.lock(fre_871/10**6)
            laser_871_lock.lock_on()

            # wait for 871 to be locked
            while not is_871_locked(fre_871/10**6):
                print('wait for 871 to be locked ...')
                time.sleep(1)

            for j in range(aom_N):
                index = i*aom_N+j
                AOM_435 = init_aom_fre+aom_scan_step*j

                # change AOM frequency
                code = "conda activate base && python dds.py " + str(AOM_435)
                os.system(code)

                # run detection and save data
                temp = self.run_sequence()

                y_data1 = y_data1[1::]+[temp[0]]
                y_data2 = y_data2[1::]+[temp[1]]

                # print information
                data_item = [AOM_435, temp[0], temp[1], wm.get_data()[0]]
                data[:, index] = data_item

                # write data
                content = str(data[0, index])+','+str(data[1, index]) + \
                    ','+str(data[2, index])+','+str(data[3, index])+','+str(fre_871)+'\n'
                file_write(file_name, content)

                #
                print('coming to line 298')
                print_info(data_item)
                pbar.update(10*index+1)
                print('\n')

                # rescan at most n times when effiency is less than 80%
                rescan_time = 0
                temp_data = []

                if temp[0] < 90:
                    while rescan_time < 5:
                        # check if there is ion
                        ccd_on()
                        time.sleep(0.5)

                        # there is ion try to cool the ion
                        if has_ion():
                            shutter_370.on()
                            time.sleep(0.5)
                            shutter_370.off()
                            pmt_on()
                            time.sleep(0.2)
                            temp1 = self.run_sequence()
                            temp_data.append(list(temp1))
                            rescan_time += 1
                            print('rescan:%d, effiency:%d' %
                                  (rescan_time, temp1[0]))
                            print('\n')

                        # there is no ion reload ion
                        else:
                            reload_ion()
                            pmt_on()

                if rescan_time == 5:
                    # print('saveing data')
                    temp_data = np.array(temp_data, dtype=np.int)
                    effiencies = temp_data[:, 0]
                    counts = temp_data[:, 1]

                    rescan_content = str(AOM_435)
                    for k in range(5):
                        rescan_content = rescan_content+','+str(effiencies[k])

                    for kk in range(5):
                        rescan_content = rescan_content+','+str(counts[kk])

                    rescan_content = rescan_content+','+str(fre_871)+'\n'
                    file_write(rescan_file_name, rescan_content)

                    if effiencies.mean() < 90:
                        file_write(manual_rescan_file_name, rescan_content)

            # update figure
            # line1.set_xdata(data[0,0:index])

        file.close()
        rescan_file.close()
        manual_rescan_file.close()
        save_file(data, __file__[:-3])
