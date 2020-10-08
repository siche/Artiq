import sys
import os
import select
import mmap
import contextlib
import time
# import numpy as np
# import matplotlib.pyplot as plt

with open("data.dat", "w+") as f:
    f.write('\x00' * 4)

def write_data(data):
    with open('data.dat', 'r+') as f:
        with contextlib.closing(mmap.mmap(f.fileno(), 4, access=mmap.ACCESS_WRITE)) as m:
            data =str(data)
            m.write(data.encode('utf-8'))
            m.flush()


from artiq.experiment import *

if os.name == "nt":
    import msvcrt

# data = [0]

class test(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        #data = np.array([0])
        #time = np.array([0])
        time_now = 0.0

        while True:
            count = 0
            with parallel:
                # 如果采样时间过长(ms量级)且光子数较多会导致 OverFlow
                try:
                    self.ttl0.gate_rising(100*us)
                    count = self.ttl0.count(now_mu())
                    time_now = time_now+0.1
                    delay(10*ms)
                    time_now = time_now+0.1
                # 处理 overflow
                except:
                    delay(100*ms)
            write_data(count)
            # sys.stdout.flush()
            # 将 stdout 缓冲，使得能够在 print 输出完之前获取数据
            # print(count)
            # delay(1000*us)
