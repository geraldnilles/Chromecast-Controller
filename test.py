#!/usr/bin/env python3

import castcontroller as controller
import time

cmds = controller.Command

print(controller.client({
    "cmd":cmds.list_devs
    }))

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.stop,
    }))

time.sleep(5)

# Get Device status 3 times and time how long it takes
for x in range(3):
    a=time.time()
    print(controller.client({
        "device":"Bedroom TV",
        "cmd":cmds.status
        }))
    b=time.time()
    print(a-b)


# Adjust the volume up 3 times
for x in range(3):
    a=time.time()
    print(controller.client({
        "device":"Bedroom TV",
        "cmd":cmds.volume,
        "args":[1]
        }))
    b=time.time()
    print(a-b)

# Adjust the volume down 3 times
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
    "args":[50]
    }))

# Start playing a video
print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.play,
    "args":["http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4","video/mp4"]
    }))

# And Queue up a 2nd video
print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.play,
    "args":[
        "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "video/mp4",
        True]
    }))

# Let the device play
time.sleep(30)

# Skip ahead 60 seconds
print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.skip,
    "args":[60]
    }))

time.sleep(10)
# Skip Back 30 seconds
print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.skip,
    "args":[-30]
    }))

time.sleep(10)


print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.queue_next
    }))

time.sleep(30)

print(controller.client({
    "device":"Bedroom TV",
    "cmd":cmds.queue_prev
    }))


