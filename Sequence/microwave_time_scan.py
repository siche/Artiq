import sys
import os
import select
import numpy as np
from artiq.experiment import *
import matplotlib.pyplot as plt
if os.name == "nt":
    import msvcrt
from save_data import save_file

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')

    @kernel
    def run_sequence(self,t2):
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
        for i in range(100):
            with sequential:
                self.cooling.sw.on()
                self.detection.sw.off()
                # cooling for 1 ms
                delay(1*ms)
                self.cooling.sw.off()
                delay(1*ms)
                
                # pumping for 400us
                self.pumping.sw.on()
                delay(50*us)
                self.pumping.sw.off()
                
                # microwave on
                self.microwave.sw.on()
                delay(t2*us)
                self.microwave.sw.off()


                # detection on
                with parallel: 
                    self.detection.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()

        return (count,photon_count)

    def run(self):
        init_time = 30
        time_interval = 2
        N = 30
        data = np.zeros((3,N))
        for i in range(N):
            microwave_time = init_time + i*time_interval - N/2*time_interval
             #microwave_time = init_time + i*time_interval
            temp = self.run_sequence(microwave_time)
            data[0,i] = microwave_time

            # accuracy
            data[1,i]=temp[0]

            # count
            data[2,i]=temp[1]
            
            print("\nAccuracy:%.1f%%" % (temp[0]))
            print('Photon Count:%d' % temp[1])
            print('microwave time:%d' % microwave_time)
    
        np.save('microwave',data)
        save_file(data,__file__[:-3])
        plt.figure(1)
        ax1 = plt.subplot(121)
        ax1.bar(data[0],data[1],width=time_interval/2)
        ax1.legend('efficiency')

        ax2 = plt.subplot(122)
        ax2.bar(data[0],data[2],width=time_interval/2)
        ax2.legend('count')

        plt.show()