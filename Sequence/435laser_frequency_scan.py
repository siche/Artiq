import sys, os, msvcrt, time
import signal, atexit, win32api, win32con

import numpy as np
from tqdm import trange

from artiq.experiment import *
from save_data import save_file
from progressbar import *
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
    def run_sequence(self):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        for i in range(300):
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
                delay(1200*us)
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

        return (count, photon_count)

    def run(self):
        self.pre_set()

        pmt_on()
        init_fre = 180
        lock_point = 871.034823
        scan_step = 0.05/2
        N = 4200

        widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
                   Timer(), ' ', ETA(), ' ']
        pbar = ProgressBar(widgets=widgets, maxval=10*N).start()

        file_name = 'data\\'+str(lock_point)[5::]+'-'+str(init_fre)+'-' + \
            str(float(init_fre+N*scan_step))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        rescan_file_name = 'data\\rescan' + str(lock_point)[5::]+'-' + \
            str(init_fre)+'-'+str(float(init_fre+N*scan_step))+'.csv'
        rescan_file = open(rescan_file_name, 'w+')
        rescan_file.close()

        manual_rescan_file_name = 'data\\manual_rescan' + str(lock_point)[5::]+'-' + \
            str(init_fre)+'-'+str(float(init_fre+N*scan_step))+'.csv'
        manual_rescan_file = open(manual_rescan_file_name, 'w+')
        manual_rescan_file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_fre, init_fre+scan_step*(N-1), N)

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
            temp = self.run_sequence()

            y_data1 = y_data1[1::]+[temp[0]]
            y_data2 = y_data2[1::]+[temp[1]]

            # print information
            data_item = [AOM_435, temp[0], temp[1], wl_871]
            data[:, i] = data_item

            # write data
            content = str(data[0, i])+','+str(data[1, i]) + \
                ','+str(data[2, i])+','+str(data[3, i])+'\n'

            file_write(file_name, content)
            print_info(data_item)
            pbar.update(10*i+1)
            print('\n')

            # rescan at most n times when effiency is less than 80%
            rescan_time = 0
            temp_data = []

            # there may multiple ion
            if temp[1] > 800:
                if has_ion() > 1:
                    reload_ion()
                    pmt_on()

            if temp[0] < 70:
                while rescan_time < 5:
                    # check if there is ion
                    ccd_on()
                    time.sleep(0.8)

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

                rescan_content = rescan_content + '\n'
                file_write(rescan_file_name, rescan_content)

                if effiencies.mean() < 90:
                    file_write(manual_rescan_file_name, rescan_content)

            # update figure
            # line1.set_xdata(data[0,0:i])

        file.close()
        rescan_file.close()
        manual_rescan_file.close()
        save_file(data, __file__[:-3])
        curr.off()
