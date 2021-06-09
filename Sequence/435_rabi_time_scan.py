import sys, os, msvcrt, time
import signal, atexit, win32api, win32con

import numpy as np
from tqdm import trange

from artiq.experiment import *
from save_data import save_file
import matplotlib.pyplot as plt
from wlm_web import wlm_web

from dds2 import *
from image_processing import has_ion
from CurrentWebClient import current_web

wm = wlm_web()
wl_871 = 0.0
curr = current_web()
DDS = dds_controller('COM5')


def is_871_locked(lock_point=871.034636):
    global wl_871
    wl_871 = wm.get_channel_data(7)
    is_locked = abs(wl_871-lock_point) < 0.000005
    return is_locked

def print_info(item):
    print("Time:%.2f  Effi:%.1f%%  Count:%d" % (item[0], item[1], item[2]))
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
    def run_sequence(self, rabi_time, run_times=100):
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
        
        # AOM_435 MicroMotion = 228.4915
        # AOM_435 Red Phonon Sideband 239.0195
        # AOM_435 = 239.965-22.52968/2
        t1 = time.time()
        AOM_435 = 241.909
        DDS_AMP = 0.8
        DDS.set_frequency(frequency=AOM_435, amplitude=DDS_AMP)
        lock_point = 871.034636
        init_value = 0.0
        scan_step = 3
        N = 50
        run_times = 200
        
        file_name = 'data\\Rabi_AOM_Time_Scan'+str(init_value)+'-'+\
                     str(float(init_value+N*scan_step))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_value, init_value+scan_step*(N-1), N)

        # drive AOM
       
       
        # scab iteration
        for i in trange(N):
            scan_value = init_value+scan_step*i  # - 0.001*N/2

            # wait for 871 to be locked
            while not is_871_locked(lock_point):
                print('Laser is locking...')
                time.sleep(3)

            # run detection and save data
            temp = self.run_sequence(scan_value,run_times)

            # print information
            data_item = [scan_value, temp[0], temp[1], wl_871]
            data[:, i] = data_item

            # write data
            content = str(data[0, i])+','+str(data[1, i]) + \
                ','+str(data[2, i])+','+str(data[3, i])+'\n'

            file_write(file_name, content)
            print_info(data_item)

        file.close()
        save_file(data, file_name[5:-4])
        curr.off()
        
        t2 = time.time()
        print("Time costed:%s" %(t2-t1))
        # plot figures
        plt.figure(1)
        x1 = data[0,:]
        y1 = data[1,:]
        plt.plot(x1, y1)
        plt.show()