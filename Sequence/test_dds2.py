
# test dds

from dds2 import *
import time

dds = dds_controller('COM5')
fre = 240

for i in range(10):
    amp = 0.1*i
    print("amp:%s" % amp)
    dds.set_frequency(frequency=fre, amplitude=amp)
    time.sleep(3)