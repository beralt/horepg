horepg
======

This simple script parses EPG data from the service at horizon.tv (which is used by a product sold by a digital cable provider in the Netherlands). The original data is formatted JSON. This script translated that to the XMLTV format and passes that to TVHeadend using the 'external grabber' interface. This interface is a Unix socket which is read by TVHeadend.

The script fetches a channel list from TVHeadend, and tries to match channels found in the Horizon data to channels found in TVHeadend. As long as you keep the channel names as provided on the DVB-C network a match is very likely, and no configuration is required.

EPG data for radio channels is added using oorboekje.nl as source. This is disabled by default, and enabled by passing the '-R' option on the commandline.
j

Configuration
-------------

The script attempts to fetch a list of channels from TVHeadend using the JSON API, credentials can be passed on the commandline.

The script attempts to switch to the 'hts' user, with its group set to 'video'. This is what is default on my system, so you might want to changes this to reflect your own setup.

The script daemonizes by default, and waits 24 hours before fetching a new batch of data.


Dependencies
------------

The only dependency is the Requests package, required for Basic Authentication for authentication in TVHeadend.


Installation
------------

Use setuptools to install HorEPG:

```
python setup.py install
```

Usage
-----

```
usage: horepgd.py [-h] [-s [PATH]] [-p [PATH]] [-u [USER]] [-g [GROUP]] [-d]
                  [-tvh HOST] [-tvh_username USERNAME]
                  [-tvh_password PASSWORD] [-R]

Fetches EPG data from the Horizon service and passes it to TVHeadend.

optional arguments:
  -h, --help            show this help message and exit
  -s [PATH]             path to TVHeadend XMLTV socket
  -p [PATH]             path to PID file
  -u [USER]             run as USER
  -g [GROUP]            run as GROUP
  -d                    daemonize
  -1                    Run once, then exit
  -nr [DAYS]            Number of days to fetch
  -tvh HOST             the hostname of TVHeadend to fetch channels from
  -tvh_username USERNAME
                        the username used to login into TVHeadend
  -tvh_password PASSWORD
                        the password used to login into TVHeadend
  -R                    fetch EPG data for radio channels
```

This would require some privileges to switch to the user and group if daemonizing. The script daemonizes by default, and logging is using syslog().

Improvements
------------

- It would be nice to stop the whole reconnecting for each channel thingy.
- Maybe this should be a proper xmltv parser.
