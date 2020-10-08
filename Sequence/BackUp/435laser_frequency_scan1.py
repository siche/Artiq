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

        
    ccd_on()
    curr.off()
    shutter_370.off()
    shutter_399.off()
    curr.beep()


def fit_func(x, a, b, c, d):
    return a*np.sin(b*x+c)+d


def is_871_locked(lock_point=871.034924):
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
        self.ttl_935 = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

    @kernel
    def run_sequence(self):
        # t2 is the time of microwave

        # initialize dds
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

        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0
        for i in range(50):
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
                delay(30*us)
                self.pumping.sw.off()
                delay(1*us)

                # turn on 435 and turn off 935 sideband
                # with parallel:
                # turn off 935
                self.ttl_935.on()
                delay(1*us)

                # turn on 435
                self.ttl_435.off()
                delay(400*us)
                self.ttl_435.on()
                delay(1*us)

                # microwave on
                self.microwave.sw.on()
                delay(39*us)
                self.microwave.sw.off()

                # detection on
                with parallel:
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.detection.sw.on()
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
        pmt_on()
        init_fre = 80
        lock_point = 871.034927
        N = 3000

        widgets = ['Progress: ', Percentage(), ' ', Bar('#'), ' ',
                   Timer(), ' ', ETA(), ' ']
        pbar = ProgressBar(widgets=widgets, maxval=10*N).start()

        file_name = 'data\\'+str(init_fre)+'-' + \
            str(float(init_fre+N*0.005))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        rescan_file_name = 'data\\rescan' + \
            str(init_fre)+'-'+str(float(init_fre+N*0.005))+'.csv'
        rescan_file = open(rescan_file_name, 'w+')
        rescan_file.close()

        manual_rescan_file_name = 'data\\manual_rescan' + \
            str(init_fre)+'-'+str(float(init_fre+N*0.005))+'.csv'
        manual_rescan_file = open(manual_rescan_file_name, 'w+')
        manual_rescan_file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_fre, init_fre+0.005*(N-1), N)

        plt.figure(1)
        fig1 = plt.subplot(211)
        line1, = fig1.plot(data[0, 0:0], data[1, 0:0])

        fig2 = plt.subplot(212)
        line2, = fig2.plot(data[0, 0:0], data[2, 0:0])

        for i in range(N):
            AOM_435 = init_fre+0.005*i  # - 0.001*N/2

            # wait for 871 to be locked
            while not is_871_locked(lock_point):
                time.sleep(5)

            # change AOM frequency
            code = "conda activate base && python dds.py " + str(AOM_435)
            os.system(code)

            # run detection and save data
            temp = self.run_sequence()
            # print information
            data_item = [AOM_435, temp[0]*2, temp[1], wm.get_data()[0]]
            data[:, i] = data_item

            """
            line1.set_xdata(data[0, 0:i])
            line1.set_ydata(data[1, 0:i])
            line2.set_xdata(data[0, 0:i])
            line2.set_ydata(data[2, 0:i])

            fig1.relim()
            fig1.autoscale_view(True, True, True)
            fig2.relim()
            fig2.autoscale_view(True, True, True)
            """

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

            if 2*temp[0] < 80:
                while rescan_time < 5:
                    # check if there is ion
                
                    time.sleep(0.5)
                    shutter_370.on()
                    time.sleep(0.5)
                    shutter_370.off()
        
                    time.sleep(0.2)
                    
                    temp1 = self.run_sequence()
                    temp_data.append(list(temp1))
                    rescan_time += 1
                    print('rescan:%d, effiency:%d' %
                          (rescan_time, 2*temp1[0]))
                    print('\n')


            if rescan_time == 5:
                # print('saveing data')
                temp_data = np.array(temp_data, dtype=np.int)
                effiencies = temp_data[:, 0]

                if 2*effiencies.mean() < 80:
                    manual_rescan_content = str(AOM_435)+'\n'
                    file_write(manual_rescan_file_name, manual_rescan_content)

                rescan_content = str(AOM_435)
                for k in range(5):
                    rescan_content = rescan_content+','+str(2*effiencies[k])
                rescan_content = rescan_content + '\n'
                file_write(rescan_file_name, rescan_content)

            """
            plt.draw()
            plt.pause(1e-8)
            """
            # update figure
            # line1.set_xdata(data[0,0:i])

        file.close()
        rescan_file.close()
        manual_rescan_file.close()
        save_file(data, __file__[:-3])

        line1.set_xdata(data[0, :])
        line1.set_ydata(data[1, :])
        line2.set_xdata(data[0, :])
        line2.set_ydata(data[2, :])

        fig1.relim()
        fig1.autoscale_view(True, True, True)
        fig2.relim()
        fig2.autoscale_view(True, True, True)
        plt.show()
