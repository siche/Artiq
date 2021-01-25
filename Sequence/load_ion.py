
# auto load ion
from image_processing import has_ion
from ttl_client import shutter
from CurrentWebClient import current_web
import time
import signal,sys
import atexit

def register_data(t1):
    time_now = time.strftime("%Y-%m-%d-%H-%M")
    file = open('data\\load_time.csv','a')
    content = time_now + ',' + str(t1)
    file.write(content)
    file.close()

class IonLoader(object):
    def __init__(self):
        super(IonLoader, self).__init__()
        self.shutter_370 = shutter(com=0)
        self.flip_mirror = shutter(com=1)
        self.shutter_399 = shutter(com=2)
        self.curr = current_web()
        self.isLoading = True

        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)
        atexit.register(self.closeAll)
    def is_ion(self):
        return has_ion()

    def load_ion(self):
        self.curr.on()
        self.flip_mirror.off()
        time.sleep(0.3)
        self.flip_mirror.on()
        time.sleep(1)

        t1 = time.time()
        costed_time = 0

        while (not has_ion() and costed_time < 1200 and self.isLoading):
            self.shutter_370.on()
            self.shutter_399.on()
            t2 = time.time()
            costed_time = t2-t1
            print('\rION? %s LAODING %.1F' % (has_ion(), costed_time),end = ' ')
            # print('LOADING ... %.1fs' % costed_time)
            time.sleep(0.5)

        if costed_time > 1200:
            print('COSTEM TIME IS OUT OF MAX TIME')
            return False

        if has_ion():    
            self.flip_mirror.on()
            self.curr.off()
            self.shutter_370.off()
            self.shutter_399.off()
            self.curr.beep(3)
            register_data(costed_time)
            return True
        else:
            return False

    def reload_ion(self):
        self.shutter_370.on()
        wait_time = 5
        costed_time = 0

        while (costed_time < wait_time and not has_ion()):
            time.sleep(1)
            costed_time += 1

        if has_ion():
            self.curr.off()
            self.shutter_370.off()
            self.shutter_399.off()
            self.curr.beep(3)
        else:
            self.load_ion()

    def protect(self, is_on=True):
        if is_on:
            self.shutter_370.on()
        else:
            self.shutter_370.off()

    def exit(self, signum, frame):
        self.curr.off()
        sys.exit()
    
    def setLoad(self,isLoading=True):
        self.isLoading = isLoading
        if isLoading:
            self.curr.on()
        else:
            self.curr.off()
    

    def closeAll(self):
        self.curr.off()
    

if __name__ == '__main__':
    ion = IonLoader()
    ion.load_ion()
