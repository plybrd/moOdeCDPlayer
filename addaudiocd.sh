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

#get the track count from cdparanoia
musicbrainz.py > /var/lib/mpd/playlists/CDPlayer.m3u
if [ ! -s /var/lib/mpd/playlists/CDPlayer.m3u ]; then
  cdparanoia -vsQ 2>&1 | \
      awk '/^TOTAL/ {on=0} (on) {print $1,$3} /^=+$/ {on=1}' | \
      sed 's/\./:/' | \
      sed -E 's/[ []|\]//g' | \
      awk -F':' 'BEGIN {print "#EXTM3U";print ""}\
                       {print "#EXTINF:" int($2*60+$3) ",CD Piste",$1 ; print "cdda:///"$1;print ""}' \
      > /var/lib/mpd/playlists/CDPlayer.m3u
fi

/usr/bin/mpc -q clear
/usr/bin/mpc -q load CDPlayer
/usr/bin/mpc -q play
