
import socket
import time

class laser_lock():
    def __init__(self,ip='192.168.1.7',port=6790):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        print(s.recv(1024).decode('utf-8'))
        self.sock = s
        self.lock_off()
    
    def lock_on(self):
        self.sock.send(b'lock:True')
        print(self.sock.recv(1024).decode('utf-8'))

    def lock_off(self):
        self.sock.send(b'lock:False')
        print(self.sock.recv(1024).decode('utf-8'))
    
    def lock(self,fre):

        # enable lock 
        self.sock.send(b'lock:True')
        self.sock.recv(1024)

        code = str(fre).encode('utf-8')
        self.sock.send(code)
        self.sock.recv(1024)

    def close(self):
        self.sock.shutdown(2)
        self.sock.close()

if __name__ == '__main__':
    des_fre = 344.172670
    laser_lock_871 = laser_lock()
    while True:
        laser_lock_871.lock(des_fre)