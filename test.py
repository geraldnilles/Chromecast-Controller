import controller
import time

cmds = controller.Command

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.list_devs
    }))

for x in range(3):
    a=time.time()
    print(controller.client({
        "device":"Bedroom TV",
        "cmd":cmds.status
        }))
    b=time.time()
    print(a-b)

exit()

for x in range(3):
    a=time.time()
    print(controller.client({
        "device":"Bedroom TV",
        "cmd":cmds.volume,
        "args":[1]
        }))
    b=time.time()
    print(a-b)

for x in range(3):
    a=time.time()
    print(controller.client({
        "device":"Bedroom TV",
        "cmd":cmds.volume,
        "args":[2]
        }))
    b=time.time()
    print(a-b)

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.volume,
    "args":[0.5]
    }))

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.play,
    "args":["http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4","video/mp4"]
    }))


print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.play,
    "args":[
        "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "video/mp4",
        True]
    }))


print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.skip,
    "args":[60]
    }))

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.skip,
    "args":[-30]
    }))

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.queue_next
    }))

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.queue_prev
    }))
