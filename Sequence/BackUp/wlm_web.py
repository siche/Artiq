
import requests
import json 

class wlm_web():

    def __init__(self):
        pass
    
    def get_data(self):
        reply = requests.get("http://192.168.1.7:8888/api/")
        rawData = json.loads(reply.content.decode('utf-8'))
        return rawData['wavelengths']