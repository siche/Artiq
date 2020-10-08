# -*- coding: utf-8 -*-
"""
this class represents the Toptica DLC pro laser controller
"""

import socket
import time
        
class toptica_laser(object):
    
    def __init__(self, ip_address, timeout = None, port = 1998):
        
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        
        try:
            self._socket = socket.socket()#socket.AF_INET, socket.SOCK_STREAM)
            
            if timeout is not None:
                self._socket.settimeout(timeout)
                
            self._socket.connect((ip_address, port))
            
            print('Toptica DLC pro at ip address ' + str(self.ip_address) + ' is online')
            

        except socket.error as e:
            print('connection to Toptica DLC pro at address' + str(ip_address) + ' FAILED!')
        
        # check for system health and print the response
        self._socket.send(("(param-ref 'system-health-txt)" + "\r\n").encode('utf-8'))
        
        time.sleep(0.1)
        
        self._socket.recv(256)
         
    def set_parameter(self, command, param =''):
        
        success = self._socket.send(("(param-set! '" + str(command) + " " + str(param) + ")" + "\r\n").encode('utf-8'))
        value = self._socket.recv(256)
        
        return success
        
    def read_parameter(self, command):
        
        # send request
        self._socket.send(("(param-ref '" + str(command) + ")" + "\r\n").encode('utf-8'))
        
        # wait and receive answer
        time.sleep(0.1)
        value = self._socket.recv(256)
        
        
        # received answer needs to be translated to string
        try:
            index_stop = value.rindex(b'\n> ')           
            try:
                index_start = value[:value.rindex(b'\n> ')].rindex(b'\n> ') + len('\n> ')
            except ValueError:
                index_start = 0
        except ValueError:
            print('Error parsing the answer')

        return (value[index_start:index_stop]).decode('utf-8')
    
    def get_voltage(self):
        vol = self.read_parameter('laser1:dl:pc:voltage-set')
        return float(vol)

    def set_voltage(self, vol):
        self.set_parameter('laser1:dl:pc:voltage-set', vol)

    def set_current(self, current):
        # the unit of current is in mA
        if current < self.max_current:
            self.set_parameter('laser1:dl:cc:current-set',current)
        else:
            print('current is more than max currrent')

    def on(self):
        self.set_parameter('laser1:dl:cc:enabled')
        
    def get_status(self):
        status = self.read_parameter('laser1:emission')
        return (status == '#t') 
    
    def get_current(self):
        cc = self.read_parameter('laser1:dl:cc:current-act')
        return(float(cc))
    
    def is_on(self):
        return(self.read_parameter('laser1:emission') == '#t')
        
    @property
    def status(self):
        return (self.get_status())

    @property
    def max_vol(self):
        max_vol = self.read_parameter('lase1:dl:pc:voltage-max')
        return float(max_vol)

    @property
    def min_vol(self):
        min_vol = self.read_parameter('laser1:dl:pc:voltage-min')
        return float(min_vol)

    @property
    def max_current(self):
        max_cc = self.read_parameter('laser1:dl:cc:current-clip-limit')
        return float(max_cc)

    @property
    def current(self):
        return self.get_current()

    def lock(self,wlm_fre,des_fre):
        if (wlm_fre < 0 or not self.status):
            print('wlm or laser is off')
            return
        if (self.current > self.max_current*0.95):
            print('laser current is reaching the max current')
            return

        k_p = 100
        delta_vol = (wlm_fre-des_fre)*k_p
        
        while(delta_vol > 0.5 or delta_vol < -0.5):
            delta_vol = delta_vol/2

        vol = self.get_voltage()
        new_vol = vol+delta_vol
        self.set_voltage(new_vol)