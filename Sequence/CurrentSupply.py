
from serial import Serial
import serial
import time, signal, atexit, sys

class current_supply(object):
    def __init__(self, com='Com8'):
        ser = Serial(com, 9600, timeout=0.5)
        ser.bytesize = serial.EIGHTBITS  # Number of data bits
        ser.parity = serial.PARITY_NONE  # Enable parity checking
        ser.stopbits = serial.STOPBITS_ONE  # Number of stop bits
        try:
            ser.close()
            ser.open()
            print('open serial port')
            self.ser = ser
        except:
            raise NotImplementedError('open serial port failed')
        
        self.is_on = False
        self.max_current = 3.5
        self.max_vol = 3
        self.set_current_limit(self.max_current)
        self.set_voltage_limit(self.max_vol)
        self.set_up(3.1,3)
        self.off()
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def is_completed(self):
        self.ser.write(b'*OPC?\r\n')
        status = self.ser.readline()
        time.sleep(0.1)
        # print('command completed:%s' % (status == b'1\n'))
        return (status == b'1\n')

    def on(self):
        self.ser.write(b':OUTP ON\r\n')
        time.sleep(0.1)
        if self.is_completed():
            print('enabled')
            self.is_on = True
        else:
            print('enable failed')
    
    def off(self):
        self.ser.write(b':OUTP OFF\r\n')
        time.sleep(0.1)
        if self.is_completed():
            print('enabled')
            self.is_on = False
        else:
            print('enable failed')
    
    def trigger(self):
        self.ser.write(b':TRIG:SOUR:HOLD\r\n')
        time.sleep(0.1)
        self.ser.write(b':TRIG:IMM\r\n')
        time.sleep(0.1)
        if self.is_completed():
            print('Triggered')
        else:
            print('Trigger failed')

    def set_up(self, curr=0, vol=0):

        if curr > self.max_current:
            raise ValueError('current is out of range')

        if vol > self.max_vol:
            raise ValueError('voltage is out of range')

        code = b':APPL '+str(vol).encode('ascii')+b',' + \
            str(curr).encode('ascii')+b'\r\n'
        self.ser.write(code)
        time.sleep(0.1)
        if self.is_completed():
            print('current %s, voltage %s' % (curr, vol))
        else:
            self.reset()
            raise ValueError('set up failed')
    
    def set_current_limit(self, max_current=3.5):
        self.ser.write(b':CURR:PROT STAT ON\r\n')
        time.sleep(0.1)

        if self.is_completed():
            print('set current protection')
            code = b':CURR:PROT '+str(max_current).encode('ascii')+b'\r\n'
            print(code)

            try:
                self.ser.write(code)
                time.sleep(0.1)
            except:
                print('set current limit failed')
                raise ValueError('set current limit failed')
    

    def set_voltage_limit(self, max_vol=5):

        self.ser.write(b':VOLT:PROT:STAT ON\r\n')
        time.sleep(0.1)

        code = b':VOLT:PROT '+str(max_vol).encode('ascii')+b'\r\n'
        self.ser.write(code)
        time.sleep(0.1)

        if self.is_completed():
            print('set voltage limit to %s' % max_vol)
        else:
            self.reset()
            raise ValueError('set voltage limit failed')

    def reset(self):
        self.ser.write(b':APPL 0,0\r\n')
        time.sleep(0.1)
        if self.is_completed():
            print('set current and voltage to 0')
        else:
            # self.ser.close()
            # raise ValueError('reset failed, please turn off current supply')
            print('Reset Failed')
            
    def beep(self,beep_time=1):
        self.ser.write(b':SYST:BEEP:STAT ON\r\n')
        t = 0
        while t < beep_time:
            self.ser.write(b':SYST:BEEP\r\n')
            time.sleep(0.1)
            t = t +0.1
    
    def exit(self):
        self.off()
        self.ser.close()
        sys.exit()