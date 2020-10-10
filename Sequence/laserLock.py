
import json

from websocket import create_connection
ws = create_connection("ws://192.168.1.7:8888/fileserver/")
"""
print("Sending 'Hello, World'...")
ws.send("Hello, World")
print("Sent")
"""
print("Receiving...")
result =  ws.recv()
data = json.loads(result)
print(type(data))
print("Received '%s'" % result)
for item in data:
    print(type(item))
    print(item)
msg = json.dumps(item)
print(type(msg))
print(msg)
ws.close()
