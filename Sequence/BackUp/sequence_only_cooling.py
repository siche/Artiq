import sys
import os
import select
import numpy as np

from artiq.experiment import *
from save_data import save_file
import sys
import time
if os.name == "nt":
    import msvcrt

class KasliTester(EnvExperiment):
    def build(self):
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.dds2 = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')
        
    @kernel 
    def pre_set(self):
        self.core.break_realtime()
        self.cooling.init()
        self.detection.init()
        self.dds2.init()
        self.pumping.init()

        self.cooling.set(250*MHz)
        self.detection.set(260*MHz)
        self.pumping.set(260*MHz)

        self.detection.set_att(19.4) 
        self.cooling.set_att(16.)  
        self.pumping.set_att(25.)

    @kernel
    def run_sequence(self):
        # initialize dds
        #count = np.zeros(1000,dtype=bool)
        self.core.break_realtime()
        self.dds2.sw.off()
        

        photon_count = 0
        photon_number = 0
        count = 0
        for i in range(100):
            with sequential:
                # cooling for 1 ms
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()

                # detection on
                with parallel: 
                    self.cooling.sw.on()
                    self.pmt.gate_rising(400*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                        
        
        self.detection.sw.off()
        self.cooling.sw.on()
        #self.pumping.sw.off()

        return (count,photon_count)

    def run(self):
        self.pre_set()
        repeat_time = 1000
        data = [None]*repeat_time
        for i in range(repeat_time):
            t1 =time.time()
            temp_data = self.run_sequence()
            t2 = time.time()
            print("\nAccuracy:%.1f%%" % (temp_data[0]))
            print('Photon Count:%d' % temp_data[1])
            print('Costed time:%.1fs' % (t2-t1))
            data[i] = temp_data[0]
        
        save_file(data,__file__[:-3])
       # np.save('data',np.array(data))