
# dds controller
import struct
from serial import Serial
from numpy import floor,pi
import sys

def num_to_uint(num,data_type='frequency'):

    if data_type == 'frequency':
        temp1 = num/1000*2**32
        a=int(floor(temp1/2**24))

        temp2 = temp1-a*2**24
        b=int(floor(temp2/2**16))

        temp3 = temp2-b*2**16
        c = int(floor(temp3/2**8))

        d = int(temp3-c*2**8)

        return (a,b,c,d)

    if data_type == 'amplitude':
        temp1 = int(num*2**14-1)
        a = int(floor(temp1/2**7))

        b = temp1-a*2**7
        return(a,b)

    if data_type == 'phase':
        temp1 = int(floor(num*2**16))
        a = int(floor(temp1/2**8))

        b = temp1-a*2**8
        return(a,b)

class dds_controller(object):
    def __init__(self,com='com6'):
        ser = Serial(com)
        if not ser.is_open:
            ser.open()
        self.ser = ser


    def set_frequency(self,frequency=100,amplitude=0.2,phase=0):
        if not self.ser.is_open:
            self.ser.open()
        
        # initialize
        v1 = (100,0,0,128,0,0)
        s1 = struct.pack('!{0}B'.format(len(v1)), *v1)
        self.ser.write(s1)

        v2 = (100,1,1,64,8,32)
        s2 = struct.pack('!{0}B'.format(len(v2)), *v2)
        self.ser.write(s2)

        v3 = (100,2,29,63,65,200)
        s3 = struct.pack('!{0}B'.format(len(v3)), *v3)
        self.ser.write(s3)

        v4 = (100,3,0,0,0,127)
        s4 = struct.pack('!{0}B'.format(len(v4)), *v4)
        self.ser.write(s4)

        # set frequency
        frem = num_to_uint(frequency,'frequency')
        ampm = num_to_uint(amplitude,'amplitude')
        pahsem = num_to_uint(phase,'phase')

        head = (104,14)
        v5 = head + ampm + pahsem + frem
        s5 = struct.pack('!{0}B'.format(len(v5)), *v5)
        self.ser.write(s5)

        # update
        v6 = 224
        s6 = struct.pack('!B',v6)
        self.ser.write(s6)
        self.ser.close()
        # print(ampm)

if __name__ == '__main__':
    dds1 = dds_controller('Com6')
    fre = float(sys.argv[1])
    print('435 AOM fre:%.4fMHz' % fre)
    dds1.set_frequency(fre,0.75,0)

"""
    for i in range(7):
        fre = 80 + 10*i
        dds1.set_frequency(fre,1,0)
        time.sleep(5)
"""