import controller
import time

"""
for x in range(10):
    a=time.time()
    controller.sendMsg(["Bedroom TV","status"])
    b=time.time()
    print(a-b)
"""

for x in range(10):
    a=time.time()
    controller.sendMsg(["Bedroom TV","volume",1])
    b=time.time()
    print(a-b)

for x in range(10):
    a=time.time()
    controller.sendMsg(["Bedroom TV","volume",2])
    b=time.time()
    print(a-b)
