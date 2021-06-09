import sys, os, msvcrt, time
import signal, atexit, win32api, win32con

import numpy as np
from tqdm import trange
from dds2 import *

from artiq.experiment import *
from save_data import save_file
import matplotlib.pyplot as plt
from wlm_web import wlm_web

from image_processing import has_ion
from SMB100B import SMB100B

wm = wlm_web()
wl_871 = 0.0


DDS = dds_controller('COM5')
# dds_435 = DDS_AD9910()


def is_871_locked(lock_point=871.034636):
    global wl_871
    wl_871 = wm.get_channel_data(7)
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

        # DDS port
        self.dds935 = self.get_device(dds_channel[0])
        self.light = self.get_device(dds_channel[1])
        self.dds435 = self.get_device(dds_channel[2])

        # Rf switch
        self.pmt = self.get_device('ttl0')
        self.coolingSwitch = self.get_device('ttl4')
        self.repumpingSwitch = self.get_device('ttl5')
        self.pumpingSwitch = self.get_device('ttl6')
        self.rabiSwitch = self.get_device('ttl7')

    @kernel
    def run_sequence(self, rabi_time, run_times = 100):
        # t2 is the time of microwave

        # initialize dds
        self.core.break_realtime()

        self.light.cpld.set_profile(0)
        delay(2*us)
        self.light.sw.on()
        delay(2*us)
        self.dds935.sw.on()
        delay(2*us)

        
        with parallel:
            self.coolingSwitch.on()
            self.pumpingSwitch.off()
            self.repumpingSwitch.on()
        
        photon_count = 0
        photon_number = 0
        count = 0

        for i in range(run_times):
            with sequential:

                # cooling for 1.5 ms
                self.light.sw.on()
                delay(2.0*ms)

                # pumping
                self.light.cpld.set_profile(1)
                delay(2*us)

            
                with parallel:
                    self.coolingSwitch.off()
                    self.pumpingSwitch.on()
                
                delay(5*us)
                
                # turn off 370
                # turn off pumping EOM
                # turn off 935
                # turn off 935 EOM
                
                with parallel:
                    self.light.sw.off()
                    self.pumpingSwitch.off()
                    self.dds935.sw.off()
                    self.repumpingSwitch.off()

                delay(2*us)   
        
                # turn on 435
                self.rabiSwitch.on()
                delay(rabi_time*us)
                self.rabiSwitch.off()
                

                # detection
                # turn on 370
                # turn cooling EOM
                # turn on 935
                # turn off 935 EOM

                with parallel:
                    self.light.sw.on()
                    self.dds935.sw.on()
                    self.coolingSwitch.on()

                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                
                """
                with parallel:
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.coolingSwitch.on()
                    self.dds935.sw.on()
                    self.light.sw.on()
                    
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                """

                # recover
                # Switch to profile 0 (cooling)
                # turn on cooling EOM
                # turn on 935 EOM 
                
                with parallel:
                    self.light.cpld.set_profile(0)
                    self.coolingSwitch.on()
                    self.repumpingSwitch.on()
                
        return (100*count/run_times, photon_count)

    def run(self):

        init_fre = 241.6
        stop_fre = 242.0
        DDS_AMP = 0.8
        lock_point = 871.034636
        scan_step = 0.001
        rabi_time = 100.0

        N =int((stop_fre-init_fre)/scan_step)
        run_times = 200

        file_name = 'data\\Rabi_AOM_fre_Scan'+str(init_fre)+'-'+\
                     str(float(init_fre+N*scan_step))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_fre, init_fre+scan_step*(N-1), N)

        for i in trange(N):

            AOM_435 = init_fre+scan_step*i  # - 0.001*N/2
            DDS.set_frequency(port=0, frequency=AOM_435,
                                  amplitude=DDS_AMP, phase=0)
            # wait for 871 to be locked
            while not is_871_locked(lock_point):
                print('Laser is locking...')
                time.sleep(3)

            # change AOM frequency
            """
            code = "conda activate base && python dds.py " + str(AOM_435)
            os.system(code)
            """

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
    
        min_index = data[1,:].argmin(axis=0)
        register_frequency(data[0,min_index],data[1,min_index])

        file.close()
        save_file(data, file_name[5:-4])
                
        # plot figures
        plt.figure(1)
        x1 = data[0,:]
        y1 = data[1,:]
        plt.plot(x1, y1)
        plt.show()