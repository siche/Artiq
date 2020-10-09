
import socket
import os
import threading
import signal
import sys

class current_web():
    def __init__(self, ip='192.168.1.51', port=6789):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((ip, port))
        except:
            self.t1 = threading.Thread(target=self.runServer)
            self.t1.setDaemon(True)
            self.t1.start()
            self.sock.connect((ip, port))

        print(self.sock.recv(1024).decode('utf-8'))
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def on(self):
        self.sock.send(b'on')
        reply = self.sock.recv(1024).decode('utf-8')
        if 'ON' in reply:
            print('Trun on OEVN')
        else:
            print('TURN ON FAILED')

    def off(self):
        self.sock.send(b'off')
        reply = self.sock.recv(1024).decode('utf-8')
        if 'OFF' in reply:
            print('Trun off OEVN')
        else:
            print('TURN OFF FAILED')

    def beep(self, beep_time=0.2):
        code = 'beep ' + str(beep_time)
        self.sock.send(code.encode('utf-8'))
        reply = self.sock.recv(1024).decode('utf-8')
        if 'Beep' in reply:
            print('Beep')
        else:
            print('Beep Failed')

    def runServer(self):
        cmd = 'python \"D:/Documents/208Code/LaserLock/Ion/CurrentWebServer.py\"'
        os.system(cmd)
    
    def exit(self,signum, frame):
        self.off()
        sys.exit()