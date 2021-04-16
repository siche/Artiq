
# dds controller
import struct
from serial import Serial
from numpy import floor,pi
import sys,math
import time
def num_to_uint(num,data_type='frequency'):

    max_freq = 1000
    max_amp = 1
    max_phase = 360
    
    if data_type == 'frequency':
        freq_i = min(round(num / max_freq * 2**32),2**32-1)
        freq_B1 = math.floor(freq_i / 2**24)
        freq_i -= freq_B1 * 2**24
        freq_B2 = math.floor(freq_i / 2**16)
        freq_i -= freq_B2 * 2**16
        freq_B3 = math.floor(freq_i / 2**8)
        freq_i -=  freq_B3 * 2**8
        freq_B4 = math.floor(freq_i)
        return freq_B1, freq_B2, freq_B3, freq_B4

    if data_type == 'amplitude':
        amp = min(max_amp, num)
        amp_i = min(math.floor(amp / max_amp * 2**14) , 2**14-1)
        amp_B1 = math.floor(amp_i / 2**8)
        amp_i = amp_i - amp_B1 * 2**8
        amp_B2 = math.floor(amp_i)
        return amp_B1, amp_B2

    if data_type == 'phase':
        phase_i = min(math.floor(num / max_phase * 2**16) , 2**16-1)
        phase_B1 = math.floor(phase_i / 2**8)
        phase_i = phase_i - phase_B1 * 2**8
        phase_B2 = math.floor(phase_i)
        return phase_B1, phase_B2

class dds_controller(object):
    def __init__(self,com='com5'):
        ser = Serial(com)
        if not ser.is_open:
            ser.open()
        self.ser = ser


    def set_frequency(self,port=0,frequency=100,amplitude=0.2,phase=0):
        if not self.ser.is_open:
            self.ser.open()

        max_freq = 1000
        max_amp = 1
        max_phase = 360
    
        # encode frequency
        freq_i = min(round(frequency / max_freq * 2**32),2**32-1)
        freq_B1 = math.floor(freq_i / 2**24)
        freq_i -= freq_B1 * 2**24
        freq_B2 = math.floor(freq_i / 2**16)
        freq_i -= freq_B2 * 2**16
        freq_B3 = math.floor(freq_i / 2**8)
        freq_i -=  freq_B3 * 2**8
        freq_B4 = math.floor(freq_i)
        
        # encode amp
        amp = min(max_amp, amplitude)
        amp_i = min(math.floor(amp / max_amp * 2**14) , 2**14-1)
        amp_B1 = math.floor(amp_i / 2**8)
        amp_i = amp_i - amp_B1 * 2**8
        amp_B2 = math.floor(amp_i)
        
        # encode phase
        phase_i = min(math.floor(phase / max_phase * 2**16) , 2**16-1)
        phase_B1 = math.floor(phase_i / 2**8)
        phase_i = phase_i - phase_B1 * 2**8
        phase_B2 = math.floor(phase_i)

        # write data
        self.ser.write(struct.pack('10B',32*port+8,14,amp_B1,amp_B2,phase_B1,phase_B2,freq_B1,freq_B2,freq_B3,freq_B4))
        # time.sleep(0.1)
        # update
        self.ser.write(struct.pack('B',32*port+128))
        # turn on dds
        time.sleep(0.05)
        
        self.ser.close()
        # print(ampm)

if __name__ == '__main__':
    dds1 = dds_controller('Com5')
    amp = 0.55
    t1 = time.time()
    fre = float(sys.argv[1])
    try:   
        amp = float(sys.argv[2])
    except:
        print('set amplitue to default value')

    print('435 AOM fre:%.4fMHz Amplitude:%.2f' % (fre, amp))
    dds1.set_frequency(port=0,frequency=fre,amplitude=amp,phase=0)
    print("time cost:%.3f" % (time.time()-t1))

"""
    for i in range(7):
        fre = 80 + 10*i
        dds1.set_frequency(fre,1,0)
        time.sleep(5)
"""