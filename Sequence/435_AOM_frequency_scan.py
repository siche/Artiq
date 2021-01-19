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
from CurrentWebClient import current_web
from SMB100B import SMB100B

wm = wlm_web()
wl_871 = 0.0
curr = current_web()

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)
rf_signal = SMB100B()

ccd_on = flip_mirror.on
pmt_on = flip_mirror.off
# dds_435 = DDS_AD9910()


def reload_ion():
    t1 = time.time()
    print('RELOADING...')
    pmt_on()
    rf_signal.on()
    time.sleep(0.3)
    ccd_on()
    time.sleep(1)
    # is_there_ion = has_ion()
    costed_time = 0
    ion_num = has_ion()
    is_thermalized = False
    while (costed_time < 600 and not ion_num == 1):

        # 如果有多个ion 关闭RF放掉离子
        if ion_num > 1:
            rf_signal.off()
            time.sleep(5)
            rf_signal.on()

        # when ion_num = -1 it means that the ion is thermalized
        # therefore, turn off rf and adjust 370 to toward red direction
        if ion_num == -1:
            is_thermalized = True
            rf_signal.off()
            wm.relock(2)
            time.sleep(2)
            rf_signal.on()

        curr.on()
        shutter_370.on()
        shutter_399.on()
        time.sleep(2)

        ion_num = has_ion()
        costed_time = time.time()-t1
        print('COSTED TIME:%.1fs' % (costed_time))
    
    # adjust the 370 wavelength to initial point
    if is_thermalized:
        wm.relock(2,-0.000005)

    # if run out of time and do not catch ion
    # raise warning information for turther processing 
    if costed_time > 600 or ion_num !=1:
        curr.off()
        win32api.MessageBox(0, "Please Check 370 WaveLength","Warning", win32con.MB_ICONWARNING)

    # else there is ion 
    # turn to 435 laser scan
    pmt_on()
    curr.off()
    shutter_370.off()
    shutter_399.off()
    curr.beep()

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


@atexit.register
def closeAll():
    curr.off()


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
        init_fre = 235.43
        lock_point = 871.034665
        scan_step = 0.001
        rabi_time = 1000
        N = 50
        run_times = 200

        file_name = 'data\\Rabi_AOM_Fre_Scan'+str(init_fre)+'-'+\
                     str(float(init_fre+N*scan_step))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_fre, init_fre+scan_step*(N-1), N)

        for i in trange(N):

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

        file.close()
        save_file(data, file_name[5:-4])
        curr.off()
        
        # plot figures
        plt.figure(1)
        x1 = data[0,:]
        y1 = data[1,:]
        plt.plot(x1, y1)
        plt.show()