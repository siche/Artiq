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
    def run_sequence(self,pumping_time):
        # t2 is the time of microwave
        self.core.break_realtime()

        photon_count = 0
        photon_number = 0
        count = 0

        for i in range(100):
            with sequential:
                
                # Doppler Cooling
                self.light.sw.on()
                delay(2*ms)
                self.light.sw.off()
                # pumping 

                self.light.set_frequency(256*MHz)
                self.coolingSwitch.off()
                self.pumpingSwitch.on()
                delay(2*us)

                # puming for time
                self.light.sw.on()
                delay(pumping_time*us)
                self.light.sw.off()
                self.pumpingSwitch.off()
                delay(1*us)
                

                # delay(1*us)
                # detection on
                with parallel: 
                    self.light.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                
                # return to cooling again
                self.light.set_frequency(250*MHz)
                delay(2*us)
                self.light.sw.on()
                self.coolingSwitch.on()
        return (count,photon_count)

    def run(self):
                # dds_435 = dds_controller()
        # flip_time = 75
        # microwave_fre = 400.0
        init_time = 0.
        time_interval = 0.15
        N = 30
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
