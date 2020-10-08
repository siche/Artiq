import sys
import os
import select
import numpy as np
from artiq.experiment import *

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
        self.microwave.set(400*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(19.4) 
        self.cooling.set_att(25.)
        self.microwave.set_att(0.)
        self.pumping.set_att(25.)

        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0

        for i in range(1000):
            with sequential:

                # cooling for 1 ms
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
               
                # pumping for 400us
                self.pumping.sw.on()
                delay(400*us)
                self.pumping.sw.off()

                # microwave on
                self.microwave.sw.on()
                delay(220*us)
                self.microwave.sw.off()
                
                # detection on
                with parallel: 
                    self.detection.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 0:
                        count = count + 1
                self.detection.sw.off()

        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()
        self.pumping.sw.off()
        
        return (count,photon_count)

    def run(self):
        N = 15
        data = np.zeros((3,N))
        for i in range(N):
            temp = self.run_sequence(5*i+145)
            data[0,i]=5*i+150

            # accuracy
            data[1,i]=temp[0]/10

            # count
            data[2,i]=temp[1]
            
            print("\nAccuracy:%.1f%%" % (temp[0]/10))
            print('Photon Count:%d' % temp[1])
    
        np.save('microwave',data)