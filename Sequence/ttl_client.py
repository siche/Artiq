
import socket
import sys

class shutter(object):
    def __init__(self,ip = '192.168.1.26',port=6666,com=2):
        self.com=com
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip,port))

    def on(self):
        code = str(self.com) + ' on'
        self.sock.send(code.encode('utf-8'))
        print(self.sock.recv(1024).decode('utf-8'))

    def off(self):
        code = str(self.com) + ' off'
        self.sock.send(code.encode('utf-8'))
        print(self.sock.recv(1024).decode('utf-8'))

# test ttl-client
if __name__ == '__main__':
    shutter_399 = shutter(com=1)
    import time
    for i in range(10):
        if (i-2*(i//2)):
            shutter_399.on()
            time.sleep(0.5)
        else:
            shutter_399.off()
            time.sleep(0.5)


