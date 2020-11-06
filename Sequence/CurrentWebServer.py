
import time, socket, threading
import json

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.websocket

from tornado.ioloop import PeriodicCallback
from CurrentSupply import current_supply

"""
TODO: 
    1.use tornao instead of mutiple thread 
    2.statics the time of oven use when it's over certain time turn off the oven for pretection
    3.auto detect oven usage
    4.adjust oven current 
"""

CURR = current_supply('com9')
CURR.set_up(curr=3.1, vol=2)

MAX_LISTEN = 10
SOCK_PORT = 6789
IP = '192.168.1.51'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((IP,SOCK_PORT))
s.listen(MAX_LISTEN)

def tcp_link(sock, addr):
    print('Accept new connection from %s:%s...' % addr)
    sock.send(b'Connected to OVEN SERVER!!!')
    while True:
        state = sock.recv(1024).decode('utf-8')
        repl = 'NO COMMAND'
        if state == 'on':
            CURR.on()
            reply = 'ON RECEIVED'

        if state == 'off':
            CURR.off()
            reply='OFF RECEIVED'

        if 'beep' in state:
            command = state.split(' ')
            beep_time = float(command[-1])
            CURR.beep(beep_time)
            reply = 'Beep'

        # command is in the format
        # set curr=3.2 vol=2
        if 'set' in 'a':
            command = state.split(' ')
            for item in command:
                if 'vol' in item:
                    new_vol = float(item[-1])
                
                if 'curr' in item:
                    new_curr = float(item[-1])

            CURR.set_up(curr=new_curr, vol=new_vol)
            reply = 'CURR:{}, VOL:{}'.format(new_curr, new_vol)
        sock.send(reply.encode('utf-8'))

    sock.close()
    print('Connection from %s:%s closed' % addr)

while True:
    sock, addr = s.accept()
    t = threading.Thread(target=tcp_link, args=(sock, addr))
    t.setDaemon(True)
    t.start()

