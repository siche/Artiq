import sys
import os
import select
import numpy as np
from artiq.experiment import *
import time
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit

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
        self.microwave.set(200.*MHz)
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

                # microwave on 400us
                self.microwave.sw.on()
                delay(t2*us)
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
        N = 40
        time_interval = 5
        data = np.zeros((3,N))
        for i in range(N):
            microwave_time = 200+i*time_interval-N/2*time_interval
            temp = self.run_sequence(microwave_time)
            data[0,i] = microwave_time

            # accuracy
            data[1,i]=temp[0]/10

            # count
            data[2,i]=temp[1]
            
            print("\nAccuracy:%.1f%%" % (temp[0]/10))
            print('Photon Count:%d' % temp[1])

        # function fitting
        popt,pcov = curve_fit(fit_func,data[0],data[1])
        a=popt[0]
        b=popt[1]
        c=popt[2]
        d=popt[3]
        print('rabi frequency:%.5fkHz' % (1000*b))
        print('pi time is:%.5fus' % (np.pi/(2*b)))

        x_fit = np.arange(min(data[0]),max(data[0]),0.1)
        y_fit = fit_func(x_fit,a,b,c,d)
       
        time_now = time.strftime("%Y-%m-%d-%H-%M")
        file_name = 'data\\'+ time_now

        np.save('microwave',data)
        np.save(file_name,data)

        pd_data = pd.DataFrame(data)
        xlsx_name = 'data\\'+time_now+'.xlsx'

        writer = pd.ExcelWriter(xlsx_name)
        pd_data.to_excel(writer, 'page_1', float_format='%.5f')
        writer.save()
        writer.close()

        plt.figure(1)
        plt.bar(data[0],data[1],width=time_interval/2)
        plt.plot(x_fit,y_fit)
        plt.title('microwave time -- accuracy')

        plt.figure(2)
        plt.bar(data[0],data[2],width=time_interval/2)
        plt.title('microwave time -- count')

        plt.show()
        
        