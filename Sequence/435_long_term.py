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
rf_signal = SMB100B()

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

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
        init_fre = 235.467
        lock_point = 871.034658
        scan_step = 0.0005
        rabi_time = 100

        N = 20
        center_fre = init_fre+N*scan_step/2
        run_times = 200
        sleep_time = 5
        M = 2000

        time_now = time.strftime("%Y-%m-%d-%H-%M")
        file_name = 'data\\435_long_term'+time_now+'.csv'
        file = open(file_name, 'w+')
        file.close()

        t0 = time.time()
        all_data = np.zeros((3,M))

        for j in range(M):
            
            data = np.zeros((4, N))
            data[0, :] = np.linspace(init_fre, init_fre+scan_step*(N-1), N)
            init_fre = center_fre - N*scan_step/2
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

                if temp[0] < 5:
                    reload_ion()
                    pmt_on()

                # print information
                data_item = [AOM_435, temp[0], temp[1], wl_871]
                data[:, i] = data_item
                print_info(data_item)

            t1 = time.time()
            delta_t = t1-t0

            # get the min value of effiency
            ydata = data[1,:]
            min_ind = ydata.argmin(axis=0)

            # judge if it is the random value
            """
            if min_ind > 0 and min_ind < N-1:
                if ydata[min_ind -1] < 50 and ydata[min_ind+1]<50:
                    center_fre = data[0,:][min_ind]
            """

            # save data
            all_data[0,j] = delta_t
            all_data[1,j] = data[0,:][min_ind]
            all_data[2,j] = ydata[min_ind]
        
            content = str(delta_t)+','+str(data[0,:][min_ind])+ ',' + str(ydata[min_ind])+'\n'
            file_write(file_name, content)

            time.sleep(sleep_time)
        
        file.close()
        save_file(all_data, file_name[5:-4])