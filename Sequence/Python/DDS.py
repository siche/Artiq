import serial
#import serial.tools.list_ports
import time
import math
import struct

class DDS_AD9910:
    def __init__(self,dds_ports):
        self.com_port = '' # void com port
        self.__com = ''      # void serial
        # dds port that can be used, default [0 1 2 3], this must be give at first to avoid to send command to a non-exist dds port
        self.__dds = dds_ports
        # default values for each dds
        self.__enabled = [0,0,0,0]
        self.__amplitude = [0.0,0.0,0.0,0.0]
        self.__phase = [0.0,0.0,0.0,0.0]
        self.__frequency = [10.0,10.0,10.0,10.0]    # MHz
        self.__freq_mod_first = [1,1,1,1]  # if it is the first time to change to frequency modulation mode
        
    ## Serial connection methods
    def open(self,com_port):
        # create serial connection
        print('Serial: Create a serial connection in serial port',com_port)
        try:
            self.__com = serial.Serial(com_port,timeout=1000)
        except serial.SerialException: # ???
            print('Cannot connect to DDS in serial port',com_port)
            return 1
        else:
            # only do the next things if connected
            self.com_port = com_port
            self.__initSettings()
            return 0

    def close(self):
        if len(self.com_port) != 0:
            # close serial connection
            for i_dds in self.__dds:
                self.setOnOff(i_dds,False)  # close all the channels/ports before close the connection
            print('Close serial connection')
            time.sleep(1)
            self.__com.close()
        self.__com = ''
        self.com_port = ''

    ## private methods
    ## serial communication methods & data structure conversion methods
    def __initSettings(self):
        # send initialization commands to each DDS channel/port
        # copy these commands if you what to use
        # 32*dds_port+4,0,0,128,0,0
        # 32*dds_port+4,1,1,64,8,32: 64: single tune mode
        # 32*dds_port+4,2,29,63,65,200
        # 32*dds_port+4,3,0,0,0,127
        for i_dds in self.__dds:
            self.__com.write(struct.pack('6B',32*i_dds+4,0,0,128,0,0))
            #print(struct.pack('6B',32*i_dds+4,1,1,64,8,32))
            self.__com.write(struct.pack('6B',32*i_dds+4,1,1,64,8,32))
            self.__com.write(struct.pack('6B',32*i_dds+4,2,29,63,65,200))
            self.__com.write(struct.pack('6B',32*i_dds+4,3,0,0,0,255))   ### 255 for max ouput current
        time.sleep(1)    
        # set each DDS output to disabled
        for i_dds in self.__dds:
            self.setOnOff(i_dds,False)
        print('AD9910 initialized')

    def __setChannel(self,dds_port):
        # every time the parameter of one DDS channel/port is changed, its state is updated so that the actual output state is updated
        print('AD9910: DDS',dds_port,'updated')
        # encode parameters
        freq_B1, freq_B2, freq_B3, freq_B4 = self.__encodeFreq(self.__frequency[dds_port])
        amp_B1, amp_B2 = self.__encodeAmp(self.__amplitude[dds_port])
        phase_B1, phase_B2 = self.__encodePhase(self.__phase[dds_port])
        # send commands
        if self.__enabled[dds_port]:
            print('AD9910: DDS',dds_port,'output is enbled and updated')
            print(32*dds_port+8,14,amp_B1,amp_B2,phase_B1,phase_B2,freq_B1,freq_B2,freq_B3,freq_B4)
            print(struct.pack('10B',32*dds_port+8,14,amp_B1,amp_B2,phase_B1,phase_B2,freq_B1,freq_B2,freq_B3,freq_B4).hex())
            self.__com.write(struct.pack('10B',32*dds_port+8,14,amp_B1,amp_B2,phase_B1,phase_B2,freq_B1,freq_B2,freq_B3,freq_B4))  # set parameters to register 14 of dds_port
            self.__update(dds_port)
            time.sleep(0.1)
        else:
            print('AD9910: DDS',dds_port,'output is disabled')
            self.__com.write(struct.pack('10B',32*dds_port+8,14,0,0,phase_B1,phase_B2,freq_B1,freq_B2,freq_B3,freq_B4))  # set amplitude to 0
            self.__update(dds_port)
            time.sleep(0.1)

    def __getChannel(self, dds_port):
        ## test
        self.__com.write(struct.pack('2B',32*dds_port+136, 14))    # get paramters from register 14 of dds_port
        para = self.__com.read(size = 8)   # read 8 bytes
        print(struct.unpack('8B',para))
        self.__amplitude[dds_port] = self.__decodeAmp(para[0],para[1])
        self.__phase[dds_port] = self.__decodePhase(para[2],para[3])
        self.__frequency[dds_port] = self.__decodeFreq(para[4],para[5],para[6],para[7])

    def __update(self,dds_port):
        ## update the output state of one DDS/channel
        self.__com.write(struct.pack('B',32*dds_port+128)) # update  

    def __encodeFreq(self,freq, max_freq = 1000):
        # encode a frequency value in MHz from float to 4 bytes uint8 (32bits)
        # DDS frequency range 0 - 1GHz (default)
        # actual frequency value is:
        #   1GHz *（ byte1 * 256^3 + byte2 * 256^2 + byte3 * 256 + byte4 ) / 2^32
        # max frequency bytes are 255 255 255 255
        freq_i = min(round(freq / max_freq * 2**32),2**32-1)
        freq_B1 = math.floor(freq_i / 2**24)
        freq_i -= freq_B1 * 2**24
        freq_B2 = math.floor(freq_i / 2**16)
        freq_i -= freq_B2 * 2**16
        freq_B3 = math.floor(freq_i / 2**8)
        freq_i -=  freq_B3 * 2**8
        freq_B4 = math.floor(freq_i)
        return freq_B1, freq_B2, freq_B3, freq_B4

    def __decodeFreq(self, freq_B1, freq_B2, freq_B3, freq_B4, max_freq = 1000):
        freq_B = freq_B4
        freq_B += freq_B3 * 2**8
        freq_B += freq_B2 * 2**16
        freq_B += freq_B1 * 2**24
        freq_o = max_freq*min(freq_B/(2**32),1)
        freq_o = round(freq_o,6)
        return freq_o

    def __encodeAmp(self,amp, max_amp = 1):
        # encode a amplitude value from float to 2 bytes uint8 (14bits)
        # DDS amplitude range 0 - 1 (default), the max amplitude of each DDS at different frequencies are differnet, so we use a unit value max_amp to represent them
        # actual amplitude value is:
        #   max_amp *（ byte1 * 256 + byte2 ) / 2^14
        # max amplitude bytes are 63 255
        amp = min(max_amp, amp)
        amp_i = min(math.floor(amp / max_amp * 2**14) , 2**14-1)
        amp_B1 = math.floor(amp_i / 2**8)
        amp_i = amp_i - amp_B1 * 2**8
        amp_B2 = math.floor(amp_i)
        return amp_B1, amp_B2

    def __decodeAmp(self, amp_B1, amp_B2, max_amp = 1):
        amp_B = amp_B2
        amp_B += amp_B1 * 2**8
        amp_o = max_amp*min(amp_B/(2**14),1)
        return amp_o

    def __encodePhase(self,phase, max_phase = 360):
        # encode a phase value in degree from float to 2 bytes uint8 (16bits)
        # DDS phase range 0-360 degree
        # actual Amplitude value is:
        #   360 *（ byte1 * 256 + byte4 ) / 2^16
        # max phase bytes are 255 255
        phase_i = min(math.floor(phase / max_phase * 2**16) , 2**16-1)
        phase_B1 = math.floor(phase_i / 2**8)
        phase_i = phase_i - phase_B1 * 2**8
        phase_B2 = math.floor(phase_i)
        return phase_B1, phase_B2

    def __decodePhase(self, phase_B1, phase_B2, max_phase = 360):
        phase_B = phase_B2
        phase_B += phase_B1 * 2**8
        phase_o = max_phase*min(phase_B/(2**16),1)
        return phase_o

    def __encodeTime(self,time_base, min_time = 4e-9):
        # encode a time value from float to 2 bytes uint8 (14bits)
        # DDS ramp time : max 250MHz
        # actual time value is:
        #   min_time *（ byte1 * 256 + byte2 )
        # max time bytes are 255 255
        time_i = min(math.ceil(time_base / min_time) , 2**16-1)
        time_B1 = math.floor(time_i / 2**8)
        time_i = time_i - time_B1 * 2**8
        time_B2 = math.floor(time_i)
        return time_B1, time_B2
        
    ## public methods
    ## easy to use

    ## single tune methods
    def setOnOff(self,dds_port,onoff): 
        # enable or disalbe a DDS output
        if len(self.com_port) != 0:
            print('AD9910: DDS',dds_port,'output state changed to',onoff,'.')
            self.__enabled[dds_port] = onoff
            self.__setChannel(dds_port)

    def getOnOff(self, dds_port):
        if len(self.com_port) != 0:
            if self.__enabled[dds_port]:
                self.__getChannel(dds_port)
                print('AD9910: DDS',dds_port,'output state is ',self.__enabled[dds_port],'.')
        return self.__enabled[dds_port]

    def setFrequency(self,dds_port,frequency):
        # set the frequency of a DDS in MHz
        if len(self.com_port) != 0:
            print('AD9910: DDS',dds_port,'frequency changed to', frequency, 'MHz.')
            self.__frequency[dds_port] = frequency
            self.__setChannel(dds_port)

    def getFrequency(self,dds_port):
        if len(self.com_port) != 0:
            self.__getChannel(dds_port)
            print('AD9910: DDS',dds_port,'frequency is ',self.__frequency[dds_port],'.')
        return self.__frequency[dds_port]

    def setAmplitude(self,dds_port,amplitude):
        # set the amplitude of a DDS in V
        if len(self.com_port) != 0:
            print('AD9910: DDS',dds_port,'amplitude changed to', amplitude, '.')
            self.__amplitude[dds_port] = amplitude
            self.__setChannel(dds_port)

    def getAmplitude(self,dds_port):
        if len(self.com_port) != 0:
            if self.__enabled[dds_port]:
                self.__getChannel(dds_port)
                print('AD9910: DDS',dds_port,'amplitude is ',self.__amplitude[dds_port],'.')
        return self.__amplitude[dds_port]

    def setPhase(self,dds_port,phase):
        # set the phase of a DDS in degree
        if len(self.com_port) != 0:
            print('AD9910: DDS',dds_port,'phase changed to', phase, 'degree.')
            self.__phase[dds_port] = phase
            self.__setChannel(dds_port)

    def getPhase(self,dds_port):
        if len(self.com_port) != 0:
            self.__getChannel(dds_port)
            print('AD9910: DDS',dds_port,'phase is ',self.__phase[dds_port],'.')
        return self.__phase[dds_port]

    def setAll(self,dds_port,onoff,frequency,amplitude,phase):
        # set all the parameters of a DDS
        if len(self.com_port) != 0:
            print('AD9910: DDS',dds_port,'reset.')
            self.__enabled[dds_port] = onoff
            self.__frequency[dds_port] = frequency
            self.__amplitude[dds_port] = amplitude
            self.__phase[dds_port] = phase
            self.__setChannel(dds_port)

    def getAll(self,dds_port):
        if len(self.com_port) != 0:
            self.__getChannel(dds_port)
            print('AD9910: DDS',dds_port,'get status')
        return self.__enabled[dds_port], self.__frequency[dds_port], self.__amplitude[dds_port], self.__phase[dds_port]

    ## frequency ramp modulation
    def setFreqRamp(self, dds_port, freq_up, freq_down, step_up, time_up, step_down = -1.0, time_down = -1.0):
        # freq up/down limit: MHz
        # step up/down: MHz
        # time up/down: real time for single up/down: second
        # if step_down or time_down not given, their are equal with their up ones 
        if len(self.com_port) != 0:
            print('Set frequency ramp modulation parameters (testing).')
            freq_up_B1, freq_up_B2, freq_up_B3, freq_up_B4 = self.__encodeFreq(freq_up) 
            freq_down_B1, freq_down_B2, freq_down_B3, freq_down_B4 = self.__encodeFreq(freq_down)
            print(32*dds_port+8,11,freq_up_B1, freq_up_B2, freq_up_B3, freq_up_B4, freq_down_B1, freq_down_B2, freq_down_B3, freq_down_B4)
            print(struct.pack('10B', 32*dds_port+8,11,freq_up_B1, freq_up_B2, freq_up_B3, freq_up_B4, freq_down_B1, freq_down_B2, freq_down_B3, freq_down_B4).hex())
            self.__com.write(struct.pack('10B', 32*dds_port+8,11,freq_up_B1, freq_up_B2, freq_up_B3, freq_up_B4, freq_down_B1, freq_down_B2, freq_down_B3, freq_down_B4))
            time.sleep(0.1)

            if step_down == -1.0:
                step_down = step_up
            step_up_B1, step_up_B2, step_up_B3, step_up_B4 = self.__encodeFreq(step_up) 
            step_down_B1, step_down_B2, step_down_B3, step_down_B4 = self.__encodeFreq(step_down)
            print(32*dds_port+8,12, step_up_B1, step_up_B2, step_up_B3, step_up_B4, step_down_B1, step_down_B2, step_down_B3, step_down_B4)
            print(struct.pack('10B',32*dds_port+8,12, step_up_B1, step_up_B2, step_up_B3, step_up_B4, step_down_B1, step_down_B2, step_down_B3, step_down_B4).hex())
            self.__com.write(struct.pack('10B',32*dds_port+8,12, step_up_B1, step_up_B2, step_up_B3, step_up_B4, step_down_B1, step_down_B2, step_down_B3, step_down_B4))
            time.sleep(0.1)

            if time_down == -1.0:
                time_down = time_up
            freq_range = abs(freq_up - freq_down)
            time_up_B1, time_up_B2 = self.__encodeTime(time_up*step_up/freq_range) 
            time_down_B1, time_down_B2 = self.__encodeTime(time_down*step_up/freq_range)
            print(32*dds_port+4,13, time_up_B1, time_up_B2,time_down_B1, time_down_B2)
            print(struct.pack('6B',32*dds_port+4,13, time_up_B1, time_up_B2,time_down_B1, time_down_B2).hex())
            self.__com.write(struct.pack('6B',32*dds_port+4,13, time_up_B1, time_up_B2,time_down_B1, time_down_B2))
            time.sleep(1)
            

    ## set running mode
    def setMode(self, dds_port, running_mode):
        # enable or disable ramp modulation
        if len(self.com_port) != 0:
            if running_mode == 'Single tune':
                print('Single tune')
                print(struct.pack('6B',32*dds_port+4,1,1,64,8,32).hex())
                self.__com.write(struct.pack('6B',32*dds_port+4,1,1,64,8,32)) # 64 -- hex 4e: single tune
                time.sleep(1)
                self.__update(dds_port)
            elif running_mode == 'Freq ramp mod':
                print('Frequency ramp modulation')
                print(struct.pack('6B',32*dds_port+4,1,1,78,8,32).hex())
                if self.__freq_mod_first[dds_port]:
                    self.__com.write(struct.pack('6B',32*dds_port+4,1,1,78,8,32)) # 78 -- hex 4e: freq ramp mod
                    time.sleep(1)
                    self.__update(dds_port)
                    self.__com.write(struct.pack('6B',32*dds_port+4,1,1,64,8,32)) # 78 -- hex 4e: freq ramp mod
                    time.sleep(1)
                    self.__update(dds_port)
                    self.__freq_mod_first[dds_port] = 0
                self.__com.write(struct.pack('6B',32*dds_port+4,1,1,78,8,32)) # 78 -- hex 4e: freq ramp mod
                time.sleep(1)
                self.__update(dds_port)
            else:
                print('No such running mode')


if __name__ == "__main__":
    dds = DDS_AD9910([0])
    dds.open('com5')
    t1 =time.time()
    fre = 241.783
    amp = 0.6
    dds.setFrequency(dds_port=0,frequency=fre)
    dds.setAmplitude(dds_port=0,amplitude=amp)
    dds.setOnOff(dds_port=0,onoff=True)
    print("Time cost:%.3f" % (time.time()-t1))
                                                                                                                                                                                                           