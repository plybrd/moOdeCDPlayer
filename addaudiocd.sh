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

CDPLAYLIST=/var/lib/mpd/playlists/CDPlayer.m3u

/usr/bin/eject -x $(/usr/bin/eject -X)
/usr/bin/cd-info | cd-info_m3u.awk > $CDPLAYLIST
status=$?

if (( status == 2 )); then
   musicbrainz.py > "$CDPLAYLIST.new"
   if [ -s "$CDPLAYLIST.new" ]; then
      mv "$CDPLAYLIST.new" "$CDPLAYLIST"
   else
      rm "$CDPLAYLIST.new"
   fi
fi

/usr/bin/mpc -q clear
/usr/bin/mpc -q load CDPlayer
/usr/bin/eject -x 2
/usr/bin/mpc -q play
