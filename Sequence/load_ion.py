
# auto load ion
from image_processing import has_ion
from CurrentWebClient import current_web
import time
import signal,sys
import atexit

def register_data(t1):
    time_now = time.strftime("%Y-%m-%d-%H-%M")
    file = open('data\\load_time.csv','a')
    content = time_now + ',' + str(t1) + '\n'
    file.write(content)
    file.close()

class IonLoader(object):
    def __init__(self):
        super(IonLoader, self).__init__()
        self.curr = current_web()
        self.isLoading = True

        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)
        atexit.register(self.closeAll)
    def is_ion(self):
        return has_ion()

    def load_ion(self):
        self.curr.on()

        t1 = time.time()
        costed_time = 0

        while (not has_ion() and costed_time < 1200 and self.isLoading):
            t2 = time.time()
            costed_time = t2-t1
            print('\rION? %s LAODING %.1F' % (has_ion(), costed_time),end = ' ')
            # print('LOADING ... %.1fs' % costed_time)
            time.sleep(0.5)

        if costed_time > 1200:
            print('COSTEM TIME IS OUT OF MAX TIME')
            return False

        if has_ion():    
            self.curr.off()
            self.curr.beep(3)
            register_data(costed_time)
            return True
        else:
            return False

    def reload_ion(self):
        wait_time = 5
        costed_time = 0

        while (costed_time < wait_time and not has_ion()):
            time.sleep(1)
            costed_time += 1

        if has_ion():
            self.curr.off()
            self.curr.beep(3)
        else:
            self.load_ion()

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
