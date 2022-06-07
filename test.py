import controller
import time

for x in range(3):
    a=time.time()
    print(controller.sendMsg(["Bedroom TV","status"]))
    b=time.time()
    print(a-b)

for x in range(3):
    a=time.time()
    print(controller.sendMsg(["Bedroom TV","volume",1]))
    b=time.time()
    print(a-b)

for x in range(3):
    a=time.time()
    print(controller.sendMsg(["Bedroom TV","volume",2]))
    b=time.time()
    print(a-b)


print(controller.sendMsg(["Bedroom TV","volume",50]))

print(controller.sendMsg(["Bedroom TV","stop"]))
