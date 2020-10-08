
import socket
class current_web():
    def __init__(self,ip='192.168.1.51',port=6789):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        print(self.sock.recv(1024).decode('utf-8'))
    
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
    
    def beep(self, beep_time = 0.2):
        code = 'beep ' + str(beep_time)
        self.sock.send(code.encode('utf-8'))
        reply = self.sock.recv(1024).decode('utf-8')
        if 'Beep' in reply:
            print('Beep')
        else:
            print('Beep Failed')
    
    def set_up(self, curr=3, vol=2):
        code = 'set curr='+str(curr)+' vol='+str(vol)
        self.sock.send(code.encode('utf-8'))
        reply = self.sock.recv(1024).decode('utf-8')
        print(reply)