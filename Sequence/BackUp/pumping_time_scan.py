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
        self.pumping.set_att(25.)
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
                delay(1*us)

                # pumping for 400us
                self.pumping.sw.on()
                delay(pumping_time*us)
                self.pumping.sw.off()
                
                # microwave on
                self.microwave.sw.on()
                delay(65*us)
                self.microwave.sw.off()
                delay(1*us)
            

                self.ttl_935.off()
                delay(1*us)
                # delay(1*us)
                # detection on
                with parallel: 
                    self.pmt.gate_rising(400*us)
                    self.detection.sw.on()
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1
                self.detection.sw.off()
                self.cooling.sw.on()
                 # turn on 935         
                #self.ttl_935.off()
        
        #self.detection.sw.off()
        #self.microwave.sw.off()
        #self.pumping.sw.off()
        

       
        return (count,photon_count)

    def run(self):
        x_data = list(range(100))
        y_data = [None]*100
        fig = plt.figure(1)
        fig, = plt.plot(x_data,y_data)
        ax = plt.gca()
        show_data = 'effiency:0'
        txt = ax.text(0.8,0.8,show_data ,verticalalignment = 'center', \
                                   transform=ax.transAxes)
        self.pre_set()
        i = 0

        for i in range(100):
            pumping_time = i
            temp = self.run_sequence(pumping_time)

            y_data[i] = temp[0]
            txt.remove()
            fig.set_ydata(y_data)
            ax.relim()
            show_data = 'effiency:'+str(temp[0])
            txt = ax.text(0.8,0.8,show_data ,verticalalignment = 'center', \
                                   transform=ax.transAxes)
            ax.autoscale_view(True, True, True)


            plt.draw()
            plt.pause(1e-15)

            print('detection effiency:%.1f%%' % (temp[0]))
            print('count:%d' % temp[1])
        plt.show()