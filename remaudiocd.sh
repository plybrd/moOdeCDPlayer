#!/bin/bash

#clear the queue
/usr/bin/mpc -q clear

rm -f /var/local/www/imagesw/current_cd

#The CD is ejected automatically when
# the system detects the eject button is pressed.
# The following ensures it can be ejected
# programmatically as well by invoking this script
if [ -b /dev/sr0 ]; then
  /usr/bin/eject /dev/sr0
elif [ -b /dev/sr1 ]; then
  /usr/bin/eject /dev/sr1
fi
