#!/usr/bin/env python3

from multiprocessing.connection import Listener, Client

# Local cache of Chromecast devices.  THis should mitigate the need to
# re-discover devices every time a command is sent 
DEVICE_CACHE = {}

# Socket Path.  This will be manaaged by a Systemd socket unit
UNIX_SOCKET_PATH = "/tmp/chromecast.socket"


def volume(cast,args):
    rc = cast.socket_client.receiver_controller
    level = args[0]

    prev = rc.status.volume_level

    # Special Cases: 1 will be mean step volume down 5%.  
    #                2 will mean volume up 5%
    #                Anything else will be interpreted as a percentage

    if (level == 1):
        # Down 5%
        level = prev - 0.05
    elif (level == 2):
        # Up 5%
        level = prev + 0.05
    else:
        level = level/100.0
        
    rc.set_volume(level)

    def cb_fun(status):
        logging.info("Volume now set to "+str(rc.status.volume_level))
    rc.update_status(cb_fun)

def check_status(cast):
    rc = cast.socket_client.receiver_controller
    def cb_fun(status):
        logging.info("Current App: " + repr(rc.status.app_id))
        logging.info("Chromecast Status: " + repr(rc.status))
    rc.update_status(cb_fun)
        
"""
    def show(self,name, num):
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

def stop(cast):
    cast.quit_app()

def parse_command(msg):

    device_name = msg[0]
    cmd = msg[1]
    args = msg[2:]

    if device_name in DEVICE_CACHE:
        cast = pychromecast.get_chromecast_from_host(DEVICE_CACHE[device_name])
        cast.wait()
    else:
        logging.error("Device Not Found")
        return

        
    if cmd == "reset":
        logging.info("Reconnectig to Chromecast...")
        stop(cast)
        sys.exit(1)
        return

    if cmd == "stop":
        logging.info("Stopping")
        stop(cast)
        return

    if cmd == "status":
        logging.debug("Checking Status")
        check_status(cast)
        return

    if cmd == "volume":
        logging.info("Adjusting Volume")
        volume(cast,args) 
        return

    if cmd == "show":
        logging.info("Starting a Show")
        show(cast,args) 
        return

    logging.error("Invalid Command")

def find_devices():

    # Use the script from my "discovery" package to utilize the already-running
    # Avahi daemon to find devices rather than use the python Zeroconf library
    # (which is problematic)
    for line in subprocess.check_output(["./find_chromecasts"]).decode("utf-8").split("\n"):
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


def main():
    find_devices()

    with Listener(UNIX_SOCKET_PATH , authkey=b'secret password') as listener:
        while True:
            # Set a 30s timeout and reset it each time a new message is recieved
            signal.alarm(30)
            with listener.accept() as conn:
                cmd = conn.recv()
                logging.debug(repr(cmd))
                parse_command(cmd)
                conn.send("OK")


# This is a function can be used by clients on other machines to send messages
# to this controller
def sendMsg(obj):
    with Client(UNIX_SOCKET_PATH , authkey=b'secret password') as conn:
        conn.send(obj) 
        resp = conn.recv()
        return resp

    
def alarm_handler(signum, frame):
    print("Timeout")
    sys.exit()

if __name__ == "__main__":
    # Most of these are only needed by the server so importing is done in the
    # main function to reduce memory impact for the clients.

    import signal
    import sys
    import pychromecast

    import time
    import os
    import random
    import logging
    import socket
    import subprocess
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    signal.signal(signal.SIGALRM, alarm_handler)

    main()



