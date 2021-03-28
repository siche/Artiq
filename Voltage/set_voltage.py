import sys
import os
import select
import numpy as np

from artiq.experiment import *

if os.name == "nt":
    import msvcrt
vols = [5.0, 1.0, -0.75, 1.0, 5.0, 5.0, 1.0, -0.33, 1.0, 5.0, 0.0,0.0]
# vols = [0.5, -0.5, -0.75, -0.5, 0.2, 0.5, -0.5, -0.33, -0.5, 0.2, 0.0,0.0]
chs = [0, 2, 3, 4, 5, 8, 11, 12, 14, 15, 18, 20] 
# bias 1 is for focus micromotion compensation, and the second one is for horizontal micromotion compensation
# bias = [0.020, 0.068]
bias = [0.020, 0.068]
split = 3
for i in range(5):
    vols[i] += bias[0] + bias[1]
vols[10] += bias[0] - bias[1] + split
vols[11] += split
# vol = [5.0, 0., 1., -0.75, 1., 5.0, 0., 0., 5., 0.,0.,1.,-0.33,0.,1.,6.,0.,0.,9.]+[0.]*12+[5.]
vol = [0.0]*32
for i in range(len(vols)):
    vol[chs[i]] = vols[i] 

print('vol1:%s' % vol)
# vol = [5.0, 0, 1.0, -0.75, 1.0, 5.0, 0, 0, 5.0, 0, 0, 1.0, -0.33, 0, 1.0, 6.0, 0, 0, 9.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5.0]
def chunker(seq, size):
    res = []
    for el in seq:
        res.append(el)
        if len(res) == size:
            yield res
            res = []
    if res:
        yield res


def is_enter_pressed() -> TBool:
    if os.name == "nt":
        if msvcrt.kbhit() and msvcrt.getch() == b"\r":
            return True
        else:
            return False
    else:
        if select.select([sys.stdin, ], [], [], 0.0)[0]:
            sys.stdin.read(1)
            return True
        else:
            return False


class KasliTester(EnvExperiment):
    def build(self):
        # hack to detect artiq_run
        if self.get_device("scheduler").__class__.__name__ != "DummyScheduler":
            raise NotImplementedError(
                "must be run with artiq_run to support keyboard interaction")

        self.setattr_device("core")

        self.leds = dict()
        self.ttl_outs = dict()
        self.ttl_ins = dict()
        self.urukul_cplds = dict()
        self.urukuls = dict()
        self.samplers = dict()
        self.zotinos = dict()
        self.grabbers = dict()

        ddb = self.get_device_db()
        for name, desc in ddb.items():
            if isinstance(desc, dict) and desc["type"] == "local":
                module, cls = desc["module"], desc["class"]
                if (module, cls) == ("artiq.coredevice.ttl", "TTLOut"):
                    dev = self.get_device(name)
                    if "led" in name:  # guess
                        self.leds[name] = dev
                    else:
                        self.ttl_outs[name] = dev
                elif (module, cls) == ("artiq.coredevice.ttl", "TTLInOut"):
                    self.ttl_ins[name] = self.get_device(name)
                elif (module, cls) == ("artiq.coredevice.urukul", "CPLD"):
                    self.urukul_cplds[name] = self.get_device(name)
                elif (module, cls) == ("artiq.coredevice.ad9910", "AD9910"):
                    self.urukuls[name] = self.get_device(name)
                elif (module, cls) == ("artiq.coredevice.ad9912", "AD9912"):
                    self.urukuls[name] = self.get_device(name)
                elif (module, cls) == ("artiq.coredevice.sampler", "Sampler"):
                    self.samplers[name] = self.get_device(name)
                elif (module, cls) == ("artiq.coredevice.zotino", "Zotino"):
                    self.zotinos[name] = self.get_device(name)
                elif (module, cls) == ("artiq.coredevice.grabber", "Grabber"):
                    self.grabbers[name] = self.get_device(name)

        # Remove Urukul, Sampler and Zotino control signals
        # from TTL outs (tested separately)

        # get the device database in current follder
        ddb = self.get_device_db()
        for name, desc in ddb.items():
            if isinstance(desc, dict) and desc["type"] == "local":
                module, cls = desc["module"], desc["class"]
                if ((module, cls) == ("artiq.coredevice.ad9910", "AD9910")
                    or (module, cls) == ("artiq.coredevice.ad9912", "AD9912")):
                    sw_device = desc["arguments"]["sw_device"]
                    del self.ttl_outs[sw_device]
                elif (module, cls) == ("artiq.coredevice.urukul", "CPLD"):
                    io_update_device = desc["arguments"]["io_update_device"]
                    del self.ttl_outs[io_update_device]
                elif (module, cls) == ("artiq.coredevice.sampler", "Sampler"):
                    cnv_device = desc["arguments"]["cnv_device"]
                    del self.ttl_outs[cnv_device]
                elif (module, cls) == ("artiq.coredevice.zotino", "Zotino"):
                    ldac_device = desc["arguments"]["ldac_device"]
                    clr_device = desc["arguments"]["clr_device"]
                    del self.ttl_outs[ldac_device]
                    del self.ttl_outs[clr_device]

        # Sort everything by RTIO channel number 

        self.leds = sorted(self.leds.items(), key=lambda x: x[1].channel)
        self.ttl_outs = sorted(self.ttl_outs.items(), key=lambda x: x[1].channel)
        self.ttl_ins = sorted(self.ttl_ins.items(), key=lambda x: x[1].channel)
        self.urukuls = sorted(self.urukuls.items(), key=lambda x: x[1].sw.channel)
        self.samplers = sorted(self.samplers.items(), key=lambda x: x[1].cnv.channel)
        self.zotinos = sorted(self.zotinos.items(), key=lambda x: x[1].bus.channel)
        self.grabbers = sorted(self.grabbers.items(), key=lambda x: x[1].channel_base)

    @kernel
    def set_zotino_voltages(self,zotino, voltages):
        self.core.break_realtime()
        delay(200*us)
        zotino.init()
        delay(200*us)
        i = 0
        for voltage in voltages:
            zotino.write_dac(i, voltage)
            delay(100*us)
            i += 1
        zotino.load()

    # test for the zotion voltages
    def set_voltage(self,channel, voltages):
        print("vol2:%s" % voltages)
        if self.zotinos:
            print("*** Set Voltages.")
            print("Voltages:")
            for card_n, (_, card_dev) in enumerate(self.zotinos):
                if card_n == channel:
                    print(" ".join(["{:.2f}".format(x) for x in voltages[0:10]]))
                    self.set_zotino_voltages(card_dev, voltages)
            
            print("Voltage has been set")
            #input()

    def run(self):
        print("****** Kasli system tester ******")
        print("")
        #vol = np.array([5.0,1.9235,-0.65,2.0,5.0,5.,1.9,-0.2,2.,5.]+[0.]*22)
        self.set_voltage(0,vol)