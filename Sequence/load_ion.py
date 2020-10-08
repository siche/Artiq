
# auto load ion
from image_processing import has_ion
from ttl_client import shutter
from current_client import current_web
import time

shutter_370 = shutter(com=0)
flip_mirror = shutter(com=1)
shutter_399 = shutter(com=2)

ccd_on = flip_mirror.off
pmt_on = flip_mirror.on

curr = current_web()
t1 = time.time()

def load_ion():
    curr.on()
    pmt_on()
    time.sleep(0.3)
    ccd_on()
    time.sleep(1)
    costed_time = 0

    while (not has_ion() and costed_time < 1200):
        
        shutter_370.on()
        shutter_399.on()
        t2 = time.time()
        costed_time = t2-t1
        print('ION? %s' % has_ion())
        print('LOADING ... %.1fs' % costed_time)
        time.sleep(0.5)
        
    if costed_time > 1200:
        print('COSTEM TIME IS OUT OF MAX TIME')
    ccd_on()
    curr.off()
    # shutter_370.off()
    shutter_399.off()
    curr.beep(3)

"""
it will try to reload ion when ion gets lost
step1: turn on 370-zero, wait for 10 seconds and adjust 370 to red
step2: if step1 failed
step2: load_ions
"""
def reload_ion():
    shutter_370.on()
    wait_time = 5
    costed_time = 0

    while (costed_time < wait_time and not has_ion()):
        time.sleep(1)
        costed_time += 1
    
    if has_ion():
        curr.off()
        shutter_370.off()
        shutter_399.off()
        curr.beep(3)
    else:
        load_ion()

def protect(is_on = True):
    if is_on:
        shutter_370.on()
    else:
        shutter_370.off()


if __name__ == '__main__':
    load_ion()