import numpy as np
import time
from artiq.experiment import *


class SideBandCooling(EnvExperiment):
    def build(self):

        # define HardWare device
        dds_channel = ['urukul0_ch'+str(i) for i in range(4)]
        self.setattr_device('core')
        self.detection = self.get_device(dds_channel[0])
        self.cooling = self.get_device(dds_channel[1])
        self.microwave = self.get_device(dds_channel[2])
        self.pumping = self.get_device(dds_channel[3])
        self.pmt = self.get_device('ttl0')
        self.ttl_935_AOM = self.get_device('ttl4')
        self.ttl_935_EOM = self.get_device('ttl7')
        self.ttl_435 = self.get_device('ttl6')

        # define dataset
        self.set_dataset("SBC Data", np.full(100, 0), broadcast=True)

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

        self.detection.set_att(20.)
        self.cooling.set_att(10.)
        self.microwave.set_att(0.)
        self.pumping.set_att(18.)
    
    """
    @kernel
    def sidebandcooling(self):
    """


    @kernel
    def sidebandcooling(self, rabi_time, run_times=200):
        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        photon_count = 0
        photon_number = 0
        count = 0

        with sequential:

            # 0.0 doppler cooling
            self.cooling.sw.on()
            delay(1*ms)
            self.cooling.sw.off()
            delay(1*us)

            # pumping
            self.pumping.sw.on()
            delay(50*us)
            self.pumping.sw.off()
            delay(1*us)

            # sideband cooling
            # 1. turn off 935 sideband and turn on 435 for
            #    some cooling time
            for i in range(50):
                with parallel:
                    # 1.1 turn off 935 sideband
                    self.ttl_935_EOM.on()

                    # 1.1 (in the same time) turn on 435
                    # TODO:DDS profile 的切换
                    # self.switch_to_red()
                    self.ttl_435.off()
                delay(100*us)

                # 1.2 Pumping Back
                self.ttl_935_EOM.on()
                delay(50*us)

            # 3 cooling result detection
            # Mainly detect the red sideband
            self.pumping.sw.on()
            delay(50*us)
            self.pumping.sw.off()

            for i in range(100):
                scan_time = 2*i
                for j in range(100):
                    self.ttl_935_EOM.on()

                    self.ttl_435.off()
                    delay(scan_time*us)
                    self.ttl_435_on()

                    with parallel:
                        self.pmt.gate_rising(300*us)
                        self.cooling.sw.on()
                        photon_number = self.pmt.count(now_mu())
                        photon_count = photon_count + photon_number
                        if photon_number > 1:
                            count = count + 1
                    self.ttl_935_EOM.on()
                self.mutate_dataset("SBC Data",i,count)



        for i in range(50):
            with sequential:

                # cooling for 1.5 ms
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
                delay(1*us)

                # pumping
                self.pumping.sw.on()
                delay(50*us)
                self.pumping.sw.off()
                delay(1*us)

                # turn on 435 and turn off 935 sideband
                # with parallel:
                # turn off 935 sideband

                # turn off 935
                # turn off 935 sideband
                self.ttl_935_EOM.on()
                self.ttl_935_AOM.on()
                delay(1*us)

                # turn on 435
                self.ttl_435.off()
                delay(rabi_time*us)
                self.ttl_435.on()
                delay(1*us)

                # microwave on
                """
                self.microwave.sw.on()
                delay(26.1778*us)
                self.microwave.sw.off()
                """
                # turn on 935 without sideband
                self.ttl_935_AOM.off()

                # detection on
                with parallel:
                    # self.detection.sw.on()
                    # 利用cooling  光作为detection
                    self.pmt.gate_rising(300*us)
                    self.cooling.sw.on()
                    photon_number = self.pmt.count(now_mu())
                    photon_count = photon_count + photon_number
                    if photon_number > 1:
                        count = count + 1

                # turn on 935 sideband
                self.ttl_935_EOM.off()
                self.cooling.sw.on()
        all_cout = [0]*100
        for j in range(100):
            scan_time = 10*j

        return (100*count/run_times, photon_count)

    @kernel
    def sidebandcooling(self, cooling_time, cooling_cycles):

        # initialize dds
        self.core.break_realtime()
        self.microwave.sw.off()
        self.pumping.sw.off()

        for i in range(cooling_cycles):
            with sequential:

                # cooling for 1.5 ms
                """
                self.cooling.sw.on()
                delay(1*ms)
                self.cooling.sw.off()
                delay(1*us)
                """

                # pumping
                self.pumping.sw.on()
                delay(50*us)
                self.pumping.sw.off()
                delay(1*us)

                # turn on 435 and turn off 935 sideband

                # turn off 935
                # turn off 935 sideband
                self.ttl_935_EOM.on()
                self.ttl_935_AOM.on()
                delay(1*us)

                # turn on 435
                self.ttl_435.off()
                delay(cooling_time*us)
                self.ttl_435.on()
                delay(1*us)

                # pumping back to ground state
                # turn on 935 sideband
                self.ttl_935_AOM.on()
                self.ttl_935_EOM.off()

    def run(self):

        # AOM_435 MicroMotion = 228.4915
        # AOM_435 Red Phonon Sideband 239.0195
        # AOM_435 Blue Sideband

        AOM_435 = 239.912
        AOM_435_RED_SIDEBAND = 238.381
        lock_point = 871.034644
        init_value = 0
        scan_step = 1
        N = 500
        run_times = 200
        amp = 0.9

        cooling_time = 40
        cooling_cycles = 200

        self.pre_set()
        pmt_on()

        file_name = 'data\\Carrier_After_Cooling'+str(init_value)+'-' +\
            str(float(init_value+N*scan_step))+'.csv'
        file = open(file_name, 'w+')
        file.close()

        data = np.zeros((4, N))
        data[0, :] = np.linspace(init_value, init_value+scan_step*(N-1), N)

        # SIDEBAND COOLING
        code = "conda activate base && python dds.py " + \
            str(AOM_435_RED_SIDEBAND) + ' ' + str(amp)
        os.system(code)

        # satrt cooling
        self.sidebandcooling(cooling_time, cooling_cycles)

        # scan to test if carrier becomes better
        # scan iteration
        code = "conda activate base && python dds.py " + \
            str(AOM_435) + ' ' + str(amp)
        os.system(code)

        for i in trange(N):

            """
            #SIDEBAND COOLING
            code = "conda activate base && python dds.py " + \
                str(AOM_435_RED_SIDEBAND) + ' ' + str(amp)
            os.system(code)

            # satrt cooling
            self.sidebandcooling(cooling_time, cooling_cycles)
            """

            code = "conda activate base && python dds.py " + \
                str(AOM_435) + ' ' + str(amp)
            os.system(code)
            scan_value = init_value+scan_step*i  # - 0.001*N/2

            # wait for 871 to be locked
            while not is_871_locked(lock_point):
                print('Laser is locking...')
                time.sleep(3)

            # run detection and save data
            temp = self.run_sequence(scan_value)

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

        # plot figures
        plt.figure(1)
        x1 = data[0, :]
        y1 = data[1, :]
        plt.plot(x1, y1)
        plt.show()
