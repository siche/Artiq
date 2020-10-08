import time

from image_processing import has_ion
from ttl_client import shutter

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

ccd_on = flip_mirror.off
pmt_on = flip_mirror.on

t = 0.6

pmt_on()
time.sleep(t)

for i in range(10):
    ccd_on()
    time.sleep(t)
    if not has_ion():
        print('There is no ion')
    
    pmt_on()
    time.sleep(0.6)