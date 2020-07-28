
import socket
import time
import numpy as np
import json


class wlm_web():

    def __init__(self):
        self.ip = '192.168.1.7'
        self.port = 9000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        print(self.sock.recv(1024).decode('utf-8'))
        # self.sock = s1

    def get_frequencies(self):
        self.sock.send('frequency'.encode('utf-8'))
        wlmdata = self.sock.recv(1024).decode('utf-8')
        # global wlm_data
        wlm_data = json.loads(wlmdata)
        return wlm_data

    def get_wavelengths(self):
        self.sock.send(' '.encode('utf-8'))
        wlmdata = self.sock.recv(1024).decode('utf-8')
        # global wlm_data
        wlm_data = json.loads(wlmdata)
        return wlm_data
    
    def get_data(self):
        self.sock.send(' '.encode('utf-8'))
        wlmdata = self.sock.recv(1024).decode('utf-8')
        # global wlm_data
        wlm_data = json.loads(wlmdata)
        return wlm_data
    
