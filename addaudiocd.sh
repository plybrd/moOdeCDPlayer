#!/bin/bash
# moOdeCDPlay V0.1 script

# make drive readable, just in case
# (allow for odd enumeration)
if [ -b /dev/sr0 ]; then
   chmod 644 /dev/sr0
elif [ -b /dev/sr1 ]; then
   chmod 644 /dev/sr1
else
  exit 1
fi

moodecdplayer --on-insert
