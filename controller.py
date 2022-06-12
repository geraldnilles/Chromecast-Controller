#!/usr/bin/env python3

import socket
import struct
import json
from enum import IntEnum, auto


# Local cache of Chromecast devices.  THis should mitigate the need to
# re-discover devices every time a command is sent 
DEVICE_CACHE = {}

# Socket Path.  This will be manaaged by a Systemd socket unit
UNIX_SOCKET_PATH = "/run/chromecast.socket"

class Command(IntEnum):
    play = auto()
    stop = auto()
    skip = auto()
    status = auto()
    volume = auto()
    reset = auto()
    find_devs = auto()
    list_devs = auto()
    queue_next = auto()
    queue_prev = auto()

def volume(conn,cast,args):
    logging.info("Adjusting Volume")
    rc = cast.socket_client.receiver_controller

    # THis callback will repot the final volume level
    def cb_done(status):
        logging.debug("Volume now set to "+str(rc.status.volume_level))
        sendMsg(conn,rc.status.volume_level)

    # This call back will get the inital volume level
    def cb_init(status):
        logging.debug("Volume initially set to to "+str(rc.status.volume_level))
        prev = rc.status.volume_level
        level = args[0]

        # Special Cases: 1 will be mean step volume down 5%.  
        #                2 will mean volume up 5%
        #                Anything else will be interpreted as a percentage (0 to 100)

        if (level == 1):
            # Down 5%
            level = prev - 0.05
        elif (level == 2):
            # Up 5%
            level = prev + 0.05
        else:
            level = level/100.0
        
        rc.set_volume(level)
        rc.update_status(cb_done)

    rc.update_status(cb_init)
    return True

def queue_next(conn,cast,args):
    """
    Jumps to the next video in the queue
    """
    logging.info("Jumping to Next Video")
    mc = cast.media_controller.queue_next()

def queue_prev(conn,cast,args):
    """
    Jumps to the previous video in the queue
    """
    logging.info("Jumping to Previous Video")
    mc = cast.media_controller.queue_prev()

def skip(conn,cast,args):
    logging.info("Skipping Video")
    rc = cast.socket_client.receiver_controller
    mc = cast.media_controller
    
    # THis callback will repot the final volume level
    def cb_done(status):
        logging.debug("Video position now at "+str(mc.status.current_time))
        sendMsg(conn,mc.status.current_time)

    # This call back will get the inital volume level
    def cb_init(status):
        logging.debug("Video position initially at "+str(cc.status.current_time))
        prev = mc.status.current_time
        delta_time = args[0]

        mc.seek(prev+delta_time)
        mc.update_status(cb_done)

    mc.update_status(cb_init)
    return True

def check_status(conn,cast,args):
    logging.info("Checking Status")
    rc = cast.socket_client.receiver_controller
    def cb_fun(status):
        logging.info("Current App: " + repr(rc.status.app_id))
        logging.debug("Chromecast Status: " + repr(rc.status))
        sendMsg(conn,rc.status.app_id)
    rc.update_status(cb_fun)
    return True

"""
def show(conn,cast,args):
    # Name of TV Show to start
    name = args[0]
    num = args[1]
    rc = self.device.socket_client.receiver_controller


    # If status is not set, abort and let the user try again
    # This is done to avoid an error while we wait for the system to recover
    # Idealy, id use the status callback function to send the show when ready
    if rc.status == None:
        logging.warning("Status Not Set.  Bailing")
        self.check_status()
        return
        
    # If Backdrop is the current app, the TV is likely off.  Temporarily
    # launch the media reciever in order to wake up the TV before launching
    # the show
    if rc.status.app_id == pychromecast.config.APP_BACKDROP:
        rc.launch_app(pychromecast.config.APP_MEDIA_RECEIVER)
        time.sleep(15)
    
    # Quit the current app before starting the show
    self.device.quit_app()
    time.sleep(5)

    logging.info("Playing "+ str(name))
    mc = self.device.media_controller

    # Get the aboslute path
    lib_path = os.path.abspath(
        # Jump back 1 directory and into the selcted show folder
        os.path.join(
            # Strip out the basename
            os.path.dirname(
                # Path of current file
                os.path.abspath(__file__)
            )
        ,"..","library",name )
        )
    try:
        eps = sorted(os.listdir(lib_path))
    except:
        print("Show was not found")
        eps = []

    # TODO Sort the episodes by name


    # If number of library episodes is more than "num", then randomly
    # select a chunk of sequential episodes
    if len(eps) > num:
        i = random.randrange(len(eps)-num+1)
        sel = eps[i:i+num]
    else:
        #If not, select the entire epsidoe list
        sel = eps

    # We want the first video to be nromal. and all subsequent videos be
    # enqueued
    # TODO Dynamically look up the local IP address
    enqueue = False
    for e in sel:
        if enqueue:
            logging.info ("Queueing up "+e)
            mc.play_media("http://"+socket.gethostname()+".lan:8080/library/"+name+"/"+e,
                            'video/mp4', enqueue=enqueue)
        else:
            logging.info ("Starting with "+e)
            mc.play_media("http://"+socket.gethostname()+".lan:8080/library/"+name+"/"+e,
                            'video/mp4', enqueue=enqueue)
            mc.block_until_active(10)
            enqueue = True
            time.sleep(2)
"""

def play(conn,cast,args):
    rc = cast.socket_client.receiver_controller
    mc = cast.media_controller
    if len(args > 0:
        url = args[0]
        logging.info("Playing a video:",url)
    else:
        logging.error("Invalid Command: URL not provided")
        sendMsg(conn,"OK")
        
    if len(args > 1):
        mime = args[1]
    else:
        mime = "video/mp4"

    logging.debug("MIME set to:",mime)
    if len(args) > 2:
        enqueue = args[2]
        logging.debug("Video being enqueued to the end")
    else:
        enqueue = False

    def cb_fun(status):
        logging.debug("Playback Request Complete")
        sendMsg(conn,"OK")

    mc.play_media(url,mime, callback_function=cb_fun )
    return True


def stop(conn,cast,args):
    cast.quit_app()
    return False

def parse_command(conn,msg):

    if "command" not in msg:
        logging.error("No Command Provided")
        sendMsg(conn,"Error: No Command Provided")
        return


    # If a device name was provided, make sure it is included in the cache
    if "device" in msg:
        if msg["device"] in DEVICE_CACHE:
            cast = pychromecast.get_chromecast_from_host(DEVICE_CACHE[device_name])
            cast.wait()
        else:
            logging.error("Requested Device Not Found")
            sendMsg(conn,"Error: Device not found")
            return

    else:
        cast = None

    # Run the appropriate function
    if msg["command"] not in Commands:
        logging.error("Invalid Command")
        sendMsg(conn,"Error: Invalid Command")
        return
    else:
        args = []
        if "args" in msg:
            args = msg["args"]
        wait = FunctionMap.table[msg["command"]](conn,cast,args) 

    # If 'wait' is set, wait for all the callbacks to finish before continuing
    if wait:
        while len(cast.socket_client._request_callbacks.values()) > 0:
            next(iter(cast.socket_client._request_callbacks.values()))["event"].wait()
            # Wait a extra beat for socket responses
            # TODO See if this can be removed with the new socket activation architecture
            time.sleep(0.1)

    else:
        # If wait is not set, respond with a generic "OK" without waiting
        sendMsg(conn,"OK")

def list_devices(conn,cast,args):
    """
    List devices from the cache without attempting to find new devices
    """
    sendMsg(conn, list(DEVICE_CACHE.keys()))
    # Return True since this function is generating a custom response.
    return True

def find_devices(conn=None,cast=None,args=None):
    """
    Uses Avahi to find chromecast devices and populates a local cache
    dictionary.

    The optional arguments are use in the event this is called from the
    parse_command() function
    """

    # Use the script from my "discovery" package to utilize the already-running
    # Avahi daemon to find devices rather than use the python Zeroconf library
    # (which is problematic)
    for line in subprocess.check_output(["find_chromecasts"]).decode("utf-8").split("\n"):
        if len(line) < 2:
            continue
        ip_address,name = line.split(":")

        logging.debug(ip_address, name)

        info = pychromecast.dial.get_device_info(ip_address)
        host = (ip_address, None, info.uuid, info.model_name, info.friendly_name)

        # For now, we will only store the "host" tuple in the cache. This will
        # add latency, but it will simplify the code since we will not need to
        # juggle connections. If this goes well, we can think about keeping the
        # actual connection in the cache as well
        DEVICE_CACHE[name] = host

    # If conn is not None, it was called from a webapp, so we wil respond with
    # a list of device names
    if conn:
        return list_devices(conn,cast,args)

def server(fd):
    # Populate the Device Cache with Avahi data
    find_devices()

    # Server will stop itself after 10s of inactivity
    s = socket.socket(fileno=fd)
    s.settimeout(10)

    try:
        while True:
            conn = s.accept()[0]
            obj = recvMsg(conn)
            print(obj)
            logging.debug(repr(obj))
            parse_command(conn,obj)

    except TimeoutError:
        return

def client(obj):
    # Create and connect to a Unix socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(UNIX_SOCKET_PATH)

    resp = sendRecvMsg(sock,obj)
    # TODO Close or detach?
    return resp

def recvMsg(conn):
    # Header is fixed 4 bytes
    header = conn.recv(4)
    msg_size = struct.unpack(">I",header)[0]
    body = conn.recv(msg_size)
    return json.loads(body)

def sendMsg(conn,obj):
    body = bytes(json.dumps(obj),"utf-8")
    header = struct.pack(">I",len(body))
    conn.sendall(header+body)

def sendRecvMsg(conn,obj):
    sendMsg(conn,obj)
    return recvMsg(conn)

# Builts a Lookup Table that maps enum values to their handler function
class FunctionMap: 
    table = {}
    table[Command.play] = play
    table[Command.stop] = stop
    table[Command.skip] = skip
    table[Command.status] = status
    table[Command.volume] = volume
    table[Command.reset] = reset
    table[Command.find_devs] = find_devices
    table[Command.list_devs] = list_devices
    table[Command.queue_next] = queue_next 
    table[Command.queue_prev] = queue_prev

if __name__ == "__main__":
    # Most of these are only needed by the server so importing is done in the
    # main function to reduce memory impact for the clients.

    import sys
    import pychromecast

    import time
    import os
    import random
    import logging
    import subprocess
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # Check for the Systemd Socket fileno and start a server if one exists
    from systemd.daemon import listen_fds
    fds = listen_fds()
    print(fds)
    if len(fds) > 0:
        server(fds[0])


