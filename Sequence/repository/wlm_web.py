
import requests
import json
from websocket import create_connection


class wlm_web():

    def __init__(self):
        pass

    def get_data(self):
        reply = requests.get("http://192.168.1.7:8888/api/")
        rawData = json.loads(reply.content.decode('utf-8'))
        return rawData['wavelengths']

    def get_channel_data(self, channel=1):
        reply = requests.get("http://192.168.1.7:8888/api/"+str(channel)+"/")
        return float(reply.content.decode('utf-8'))

    def unlock(self,channel=1):
        ws = create_connection("ws://192.168.1.7:8888/fileserver/")
        oldConfig = json.loads(ws.recv())

        for item in oldConfig:
            if item['channel'] == channel:
                channelConfig = item
                break

        if channelConfig:
            channelConfig["lock"] = False
            channelConfig["fre"] = str(fre)
            ws.send(json.dumps(channelConfig))

        ws.close()


    def lock(self, channel, fre=None):
        ws = create_connection("ws://192.168.1.7:8888/fileserver/")
        oldConfig = json.loads(ws.recv())

        for item in oldConfig:
            if item['channel'] == channel:
                channelConfig = item
                if fre is None:
                    fre = channelConfig["fre"]
                break

        if channelConfig:
            channelConfig["lock"] = True
            channelConfig["fre"] = str(fre)
            ws.send(json.dumps(channelConfig))

        ws.close()

    # relock laser based on present lock point
    def relock(self, channel, delta=0.000005):
        ws = create_connection("ws://192.168.1.7:8888/fileserver/")
        oldConfig = json.loads(ws.recv())

        for item in oldConfig:
            if item['channel'] == channel:
                channelConfig = item
                fre = float(channelConfig["fre"])
                break

        if channelConfig:
            channelConfig["lock"] = True
            channelConfig["fre"] = str(fre+delta)
            ws.send(json.dumps(channelConfig))

        ws.close()
