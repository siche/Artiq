import sys
import os
import select
import numpy as np
from artiq.experiment import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def fit_func(x,a,b,c):
    return 50*np.sin(a+b*x)+c

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

        self.detection.set_att(20.) 
        self.cooling.set_att(19.)
        self.microwave.set_att(0.)
        self.pumping.set_att(15.)

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
                delay(1*us)
                
                # pumping for 400us
                self.pumping.sw.on()
                delay(15*us)
                self.pumping.sw.off()
                delay(1*us)


                # microwave on
                self.microwave.sw.on()
                delay(t2*us)
                self.microwave.sw.off()

                # detection on
                with parallel: 
                    self.detection.sw.on()
                    self.pmt.gate_rising(600*us)
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

        self.cooling.sw.on()
        self.detection.sw.off()
        self.microwave.sw.off()

        return (count,photon_count)

    def run(self):
        init_time = 0
        time_interval = 1
        N = 50
        data = np.zeros((3,N))
        for i in range(N):
            microwave_time = init_time + i*time_interval
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

        # fit function
        """
        popt, pcov = curve_fit(fit_func, data[0], data[1])
        print("b:%s,b:%s,c:%s" % tuple(popt))
        plt.figure(2)
        plt.plot(data[0], data[1],'bo', label='intial data')
        xdata = np.linspace(init_time, init_time+time_interval*N,50*N)
        plt.plot(xdata, fit_func(xdata, *popt), 'r-',
        label='fit:a=%5.3f, b=%5.3f, c=%5.3f' % tuple(popt))
        plt.legend()
        """
        plt.show()