#######################
 Chromecast Controller
#######################

Many of my projects interact with Chromecast devices in my house.  I have been
using the PyChromecast library.  This library is easy to use and full-featured,
but it is pretty slow since the full stack is implemented in Python.  I tried
to improve on the performance by making persistent connections.  However, this
was rather difficult.  Chromecast connections will eventually drop and need to
be re-established.  After enough hacking, i was able to get a high performance,
long-running controller daemon,  However, it ended up having pretty nasty
memory leaks.  Each time i lost and re-established the Chromecast connection, I
was not properly cleaning up the connections.  The memory usage for this simple
process ballooned up to >1GByte after a few days.  I COULD go back and try to
fix this, but my code is so messy at this point that it would be easier to just
start over.

For this project, the Chromecast controller will be pulled out into its own
project. A single daemon can be used by any of the services instead of having
each service implement its own pyChromecast-based controller. I plan on
minimizing the cold-start latency for detecting and interacting with a
Chromecast.  By improving the performance, there wont be a need to maintain
persistent connections.  I will accomplish by using the following architecture 

 * Use Avahi to detect Chromecast instead of using the python-based Zeroconf
   library. Why reinvent the wheel when a mature, performant project already
   exists.

 * Use SystemD Sockets to spin-up the Chromecast controller on demand. Memory
   leaks will no longer be a concern since the controller will only last for a
   few seconds at a time.  After 10 or 30 seconds of inactivyt, the service
   will shutdown.  This should provide low latency for bursty events (adjusting
   volume, fast forwarding, etc..), without having to managing long-running
   connections.

 * Still use the PyChromecast library, but use the inner functions instead of
   top-level functions. The example code uses high-level functions that are
   almost guaranteed to work.  By eliminating the need to "discover" devices,
   we should be able to skip a lot of steps and go straight to communicating
   with the devices.

 * After a few seconds of inactivity, the service will be shutdown.


Other projects on this machien will be able to open a unix socket and send
commands
