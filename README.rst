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

Commands
========

Clients talk to the daemon over the systemd socket and send a JSON object::

    {"device": "<friendly name>", "cmd": <Command>, "args": [...]}

The ``cmd`` value is a member of ``castcontroller.Command`` (an ``IntEnum``,
so it serialises as an integer on the wire).

Per-episode playback
--------------------

``play`` (``args = [url, mime, enqueue]``) loads or enqueues a *single*
episode.  Enqueueing requires an already-active media session, because the
``QUEUE_INSERT`` message carries the ``mediaSessionId``.  When
``enqueue=True`` the handler therefore waits for the session to become active
before sending the command.  Note that each command gets its own connection,
so a session created by an earlier command is **not** visible to the next one.

Whole-show playback
-------------------

``play_show`` (``args = [[url1, url2, ...], mime]``) plays an ordered list of
episodes as a single continuous queue.  It uses ONE connection to:

  1. ``LOAD`` the first url (this starts the media receiver / session),
  2. wait until the media session is active,
  3. ``QUEUE_INSERT`` (``enqueue=True``) each remaining url.

This is the command the Episode Player webapp uses, and it avoids the
per-episode reconnect race where every enqueue after the first was dropped
(``mediaSessionId`` was ``null``).
