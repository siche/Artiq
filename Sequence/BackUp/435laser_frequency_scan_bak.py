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

if os.name == "nt":
    import msvcrt

def fit_func(x,a,b,c,d):
    return a*np.sin(b*x+c)+d

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
                delay(20*us)
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
                delay(34.5*us)
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
        return (count,photon_count)

    def run(self):
        
        # dds_435 = dds_controller()
        # flip_time = 75
        # microwave_fre = 400.0
        self.pre_set()
        wm = wlm_web()
        init_fre = 103
        lock_point = 871.034931
        N = 4000
        # progressbar
        widgets = ['Progress: ',Percentage(), ' ', Bar('#'),' ', Timer(),
           ' ', ETA(), ' ']
        pbar = ProgressBar(widgets=widgets, maxval=10*N).start()
        
        file_name = 'data\\'+str(init_fre)+'-'+str(float(init_fre+N*0.0005))+'.csv'
        file = open(file_name,'w+')
        file.close()

        data = np.zeros((4,N))
        for i in range(N):
            file = open(file_name,'a')
            AOM_435 =init_fre+0.0005*i #- 0.001*N/2

            wl_871 = wm.get_data()[0]
            is_871_locked = abs(wl_871-lock_point) < 0.000004
            while not is_871_locked:
                time.sleep(5)
                wl_871 = wm.get_data()[0]
                is_871_locked = abs(wl_871-lock_point) < 0.000004
            
            code = "conda activate base && python dds.py " + str(AOM_435)
            os.system(code)
            temp = self.run_sequence()
            data[0,i]=AOM_435

            # accuracy
            data[1,i]=temp[0]*2

            # count
            data[2,i]=temp[1]

            data[3,i]=wm.get_data()[0]
            
            print("Accuracy:%.1f%%" % (temp[0]*2))
            print('Photon Count:%d' % temp[1])
            pbar.update(10*i+1)
            print('\n')
            content =str(data[0,i])+','+str(data[1,i])+','+str(data[2,i])+','+str(data[3,i])+'\n'
            # print(content)
            file.write(content)
            file.close()

        np.save('microwave',data)
        file.close()
        save_file(data,__file__[:-3])

        plt.figure(1)
        ax1 = plt.subplot(121)
        ax1.plot(data[0],data[1])

        ax2 = plt.subplot(122)
        ax2.plot(data[0],data[2])
        
        plt.show()