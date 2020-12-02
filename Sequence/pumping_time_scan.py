import sys
import os
import select
import numpy as np
from artiq.experiment import *
import matplotlib.pyplot as plt


if os.name == "nt":
    import msvcrt


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
        self.ttl_pumping = self.get_device('ttl4')
    
    @kernel
    def pre_set(self):
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

        self.detection.set_att(19.0) 
        self.cooling.set_att(19.)
        self.pumping.set_att(15.)
        self.microwave.set_att(0.)

    @kernel
    def run_sequence(self,pumping_time):
        # t2 is the time of microwave
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0

        for i in range(100):
            with sequential:

                self.detection.sw.off()
                self.pumping.sw.off()
                # cooling for 1 ms
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
                delay(5*us)

                # pumping for 400us
                self.pumping.sw.on()
                delay(pumping_time*us)
                self.pumping.sw.off()
                delay(1*us)

                # delay(1*us)
                # detection on
                with parallel: 
                    self.detection.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                self.detection.sw.off()
                self.cooling.sw.on()
                self.ttl_pumping.off()
                 # turn on 935         
                #self.ttl_935.off()
        
        #self.detection.sw.off()
        #self.microwave.sw.off()
        #self.pumping.sw.off()
        

       
        return (count,photon_count)

    def run(self):
                # dds_435 = dds_controller()
        # flip_time = 75
        # microwave_fre = 400.0
        init_time = 0.
        time_interval = 1
        N = 40
        data = np.zeros((3,N))
        # pumping_time = 50.
        for i in range(N):
            pumping_time = init_time+time_interval*i
            # pumping_time = 15.0
            temp = self.run_sequence(pumping_time)
            data[0,i]=pumping_time
            data[1,i]=temp[0]*2
            data[2,i]=temp[1]
            print("%d/%d" %((i+1),N))
            print('pumping time:%.2fus\tcout:%d\teffiency:%d%%' % (pumping_time,temp[1],temp[0]))
        
        # save_file(data,__file__[:-3])
        plt.figure(1)
        
        ax1 = plt.subplot(121)
        ax1.plot(data[0],data[1])
        ax1.set_title('Detection Effiency')

        ax2 = plt.subplot(122)
        ax2.plot(data[0],data[2])
        ax2.set_title('Detection Count')
        plt.show()
