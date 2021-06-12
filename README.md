# sshguard-map
Visualize the blacklist on a map.

## Map / Output
The map visualizes the coordinates using circles. The bigger the circle, the more IP addresses are blocked from the same place. A click on the circle reveals which organization hosts the IP address and in brackets it shows the count.

## Process
1. Load the sshguard blacklist.db into an SQLite database (blacklistload.py)
2. Lookup the coordinates using Maxmind's geolocation API (blacklistlookup.py)
3. Dump the markers so that they can be visualized on the map (blacklistdump.py)
4. Open the blacklist-map.html file
