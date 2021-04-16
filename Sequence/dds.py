
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
        
        # initialize
        """
        for i in range(4):
            v1 = (32*i+4,0,0,128,0,0)
            s1 = struct.pack('!{0}B'.format(len(v1)), *v1)
            self.ser.write(s1)
            time.sleep(0.1)

            v2 = (32*i+4,1,1,64,8,32)
            s2 = struct.pack('!{0}B'.format(len(v2)), *v2)
            self.ser.write(s2)
            time.sleep(0.1)

            v3 = (32*i+4,2,29,63,65,200)
            s3 = struct.pack('!{0}B'.format(len(v3)), *v3)
            self.ser.write(s3)
            time.sleep(0.1)

            v4 = (32*i+4,3,0,0,0,127)
            s4 = struct.pack('!{0}B'.format(len(v4)), *v4)
            self.ser.write(s4)
            time.sleep(0.1)
        """
        # encode dds frequency
        frem = num_to_uint(frequency,'frequency')
        ampm = num_to_uint(amplitude,'amplitude')
        print("ampm:%s")
        print(ampm)
        print("frequency")
        print(frem)

        pahsem = num_to_uint(phase,'phase')

        head = (32*port+8,14)
        v5 = head + ampm + pahsem + frem
        s5 = struct.pack('!{0}B'.format(len(v5)), *v5)
        self.ser.write(s5)
    
        # update
        v6 = 32*port+128
        s6 = struct.pack('!B',v6)
        self.ser.write(s6)
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