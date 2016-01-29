horepg
======

This simple script parses EPG data from the service at horizon.tv (which is used by a product sold by a digital cable provider in the Netherlands). The original data is formatted JSON. This script translated that to the XMLTV format and passes that to TVHeadend using the 'external grabber' interface. This interface is a Unix socket which is read by TVHeadend.

Configuration
-------------

The script attempts to fetch a list of channels from TVHeadend using the JSON API. The current implementation requires that you allow the host running HorEPG access without authentication (this usually means allowing localhost), since there is no support for authentication at the moment.

The script attempts to switch to the 'hts' user, with its group set to 'video'. This is what is default on my system, so you might want to changes this to reflect your own setup.

Usage
-----

```
usage: horepgd.py [-h] [-s [PATH]] [-p [PATH]] [-u [USER]] [-g [GROUP]] [-d]

Fetches EPG data from the Horizon service and passes it to TVHeadend.

optional arguments:
  -h, --help  show this help message and exit
  -s [PATH]   path to TVHeadend XMLTV socket
  -p [PATH]   path to PID file
  -u [USER]   run as USER
  -g [GROUP]  run as GROUP
  -d          daemonize
```

This would require some privileges to switch to the user and group if daemonizing. The script daemonizes by default, and logging is using syslog().

Improvements
------------

- A systemd service file (or upstart) would be nice.
- It would be nice to stop the whole reconnecting for each channel thingy.
- Maybe this should be a proper xmltv parser.
