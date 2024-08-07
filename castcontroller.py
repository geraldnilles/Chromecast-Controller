#!/usr/bin/env python3

import socket
import struct
import json
from enum import IntEnum, auto
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


# Local cache of Chromecast devices.  THis should mitigate the need to
# re-discover devices every time a command is sent 
DEVICE_CACHE = {}

# Socket Path.  This will be manaaged by a Systemd socket unit
UNIX_SOCKET_PATH = "/run/chromecast.socket"

class Command(IntEnum):
    play = auto()
    stop = auto()
    skip = auto()
    seek = auto()
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

    level = args[0]

    # THis callback will repot the final volume level
    def cb_done(status,error):
        logging.debug("Volume now set to "+str(rc.status.volume_level))
        sendMsg(conn,rc.status.volume_level)

    prev = rc.status.volume_level
    if (level == 1):
        # Down 5%
        level = prev - 0.05
    elif (level == 2):
        # Up 5%
        level = prev + 0.05
    else:
        level = level/100.0
        
    rc.set_volume(level)
    rc.update_status(callback_function = cb_done)
    return True

def queue_next(conn,cast,args):
    """
    Jumps to the next video in the queue
    """
    logging.info("Jumping to Next Video")
    mc = cast.media_controller

    def cb_func(status,error):
        mc.queue_next()
        sendMsg(conn,"OK")

    # You need to update the status before you are allowed to request a queue
    # skip
    mc.update_status(callback_function = cb_func)
    return True

def queue_prev(conn,cast,args):
    """
    Jumps to the previous video in the queue
    """
    logging.info("Jumping to Previous Video")
    mc = cast.media_controller

    def cb_func(status,error):
        mc.queue_prev()
        sendMsg(conn,"OK")

    # You need to update the status before you are allowed to request a queue
    # skip
    mc.update_status(callback_function = cb_func)
    return True

def skip(conn,cast,args):
    logging.info("Skipping Video")
    rc = cast.socket_client.receiver_controller
    mc = cast.media_controller
    
    # THis callback will repot the final volume level
    def cb_done(status,error):
        logging.debug("Video position now at "+str(mc.status.current_time))
        sendMsg(conn,mc.status.current_time)

    # This call back will get the inital volume level
    def cb_init(status,error):
        logging.debug("Video position initially at "+str(mc.status.current_time))
        prev = mc.status.current_time
        delta_time = args[0]

        mc.seek(prev+delta_time)
        mc.update_status(callback_function = cb_done)

    mc.update_status(callback_function = cb_init)
    return True

def seek(conn,cast,args):
    logging.info("Seeking the Video")
    rc = cast.socket_client.receiver_controller
    mc = cast.media_controller
    
    # THis callback will repot the final volume level
    def cb_done(status,error):
        logging.debug("Video position now at "+str(mc.status.current_time))
        sendMsg(conn,mc.status.current_time)

    # This call back will get the inital volume level
    def cb_init(status,error):
        logging.debug("Video position initially at "+str(mc.status.current_time))

        mc.seek(args[0])
        mc.update_status(callback_function = cb_done)

    mc.update_status(callback_function = cb_init)
    return True

def check_status(conn,cast,args):
    logging.info("Checking Status")
    rc = cast.socket_client.receiver_controller
    def cb_fun(status,error):
        logging.info("Current App: " + repr(rc.status.app_id))
        logging.debug("Chromecast Status: " + repr(rc.status))
        sendMsg(conn,rc.status.app_id)
    rc.update_status(callback_function = cb_fun)
    return True


def play(conn,cast,args):
    rc = cast.socket_client.receiver_controller
    mc = cast.media_controller
    if len(args) > 0:
        url = args[0]
        logging.info("Playing a video: "+url)
    else:
        logging.error("Invalid Command: URL not provided")
        sendMsg(conn,"OK")
        
    if len(args) > 1:
        mime = args[1]
    else:
        mime = "video/mp4"

    logging.debug("MIME set to: "+mime)
    if len(args) > 2:
        enqueue = args[2]
        logging.debug("Video being enqueued to the end")
    else:
        enqueue = False

    def cb_fun(status,error):
        logging.debug("Playback Request Complete")
        sendMsg(conn,"OK")

    mc.play_media(url,mime, enqueue=enqueue, callback_function=cb_fun )
    return True


def stop(conn,cast,args):
    cast.quit_app()
    return False

def parse_command(conn,msg):

    if "cmd" not in msg:
        logging.error("No Command Provided")
        sendMsg(conn,"Error: No Command Provided")
        return


    # If a device name was provided, make sure it is included in the cache
    if "device" in msg:
        if msg["device"] in DEVICE_CACHE:
            cast = pychromecast.get_chromecast_from_host(DEVICE_CACHE[msg["device"]])
            cast.wait()
        else:
            logging.error("Requested Device Not Found")
            sendMsg(conn,"Error: Device not found")
            return

    else:
        cast = None

    # Run the appropriate function
    if msg["cmd"] not in Command.__members__.values():
        logging.error("Invalid Command")
        sendMsg(conn,"Error: Invalid Command")
        return
    else:
        args = []
        if "args" in msg:
            args = msg["args"]
        wait = FunctionMap.table[msg["cmd"]](conn,cast,args) 

    # If 'wait' is set, wait for all the callbacks to finish before continuing
    if wait and cast is not None:
        cast.wait()
        return

        #for key,value in cast.socket_client._request_callbacks.items():
        while cast.socket_client._request_callbacks:
            key, value = cast.socket_client._request_callbacks.popitem()
            logging.info("Callback: "+str(value))
            logging.info("Key: "+str(key))
            # Get the first callback in the dictionary
            if isinstance(value, dict) and "event" in value:
                logging.info("Dict Event")
                value["event"].wait()
            # If it is a function, then call it directly
            elif callable(value):
                logging.info("Callable")
                value(True,None)
            else:
                # If the structure is different, log it and break to avoid an infinite loop
                logging.error("Unexpected callback structure: "+str(value))
                break
            # Wait a extra beat for socket responses
            time.sleep(0.1)
    else:
        # If wait is not set, respond with a generic "OK" without waiting
        sendMsg(conn, "OK")

def reset(conn, cast, args):
    sendMsg(conn,"OK")
    exit(1)
    

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

    # By default, we will use the cached Avahi data. However, one can force a
    # refresh by adding "True" to the args list
    if args and len(args) > 0 and args[0] == True:
        # Refresh the list of devices
        cmd = ["find_chromecasts"]
    else:
        # By Default, use the cached avahi list
        cmd = ["find_chromecasts", "-c"]

    # Use the script from my "discovery" package to utilize the already-running
    # Avahi daemon to find devices rather than use the python Zeroconf library
    # (which is problematic)
    for line in subprocess.check_output(cmd).decode("utf-8").split("\n"):
        if len(line) < 2:
            continue
        ip_address,name = line.split(":")

        logging.debug(ip_address, name)

        info = pychromecast.dial.get_device_info(ip_address)

        # Only cache valid devices
        if info == None:
            continue

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
    s.settimeout(30)

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

def recvall(conn, n):
    """Helper function to recv n bytes or return None if EOF is hit"""
    data = bytearray()
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def recvMsg(conn):
    try:
        # Header is fixed 4 bytes
        header = recvall(conn, 4)
        if not header:
            logging.error("Connection closed while receiving header")
            return None
        msg_size = struct.unpack(">I", header)[0]
        body = recvall(conn, msg_size)
        if not body:
            logging.error("Connection closed while receiving body")
            return None
        return json.loads(body.decode('utf-8'))
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return None
    except struct.error as e:
        logging.error(f"Struct unpack error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in recvMsg: {e}")
        return None

def sendMsg(conn, obj):
    try:
        body = json.dumps(obj).encode('utf-8')
        header = struct.pack(">I", len(body))
        conn.sendall(header + body)
        return True
    except json.JSONEncodeError as e:
        logging.error(f"JSON encode error: {e}")
        return False
    except struct.error as e:
        logging.error(f"Struct pack error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in sendMsg: {e}")
        return False

def sendRecvMsg(conn,obj):
    sendMsg(conn,obj)
    return recvMsg(conn)

# Builts a Lookup Table that maps enum values to their handler function
class FunctionMap: 
    table = {}
    table[Command.play] = play
    table[Command.stop] = stop
    table[Command.skip] = skip
    table[Command.seek] = seek
    table[Command.status] = check_status
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
    import subprocess

    # Check for the Systemd Socket fileno and start a server if one exists
    from systemd.daemon import listen_fds
    fds = listen_fds()
    print(fds)
    if len(fds) > 0:
        server(fds[0])


