
import socket

class SMB100B(object):

    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(('192.168.1.21',5025))

        self.sock = sock
        try:
            self.sock.send(b'*IND?\r\n')
            self.sock.recv(256)
            print('Connect to SMB100B')
        except:
            print('Failed to connect to SMB100B')
    
    def on(self):
        self.sock.send(b':OUTPut:ALL:STATe 1\r\n')
    
    def off(self):
        self.sock.send(b':OUTPut:ALL:STATe 1\r\n')
