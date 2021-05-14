#!/bin/bash
# moOdeCDPlay V0.1 script

CDLIBRARY="/var/lib/moode_cd_library"
mkdir -p $CDLIBRARY

function cdinfo_playlist() {
   out=$(tempfile)
   /usr/bin/cd-info | cd-info_m3u.awk > $out
   status=$?

   if (( status == 1 )) ; then 
      exit 1  
   fi

   echo $out
   return $status
}

function musicbrainz_playlist() {
   out=$(tempfile)
   musicbrainz.py > $out
   echo $out
   return $?
}

function new_playlist() {
   playlists_1=$(cdinfo_playlist)
   status=$?
   if (( status == 2 )) ; then
      playlists_2=$(musicbrainz_playlist)
      status2=$?
      if (( status2 == 0 )) ; then
         rm -f $playlists_1
         echo $playlists_2
         return 0
      fi
      rm -f $playlists_2
   fi
   echo $playlists_1
   return $status
}

function playlists() {
   cdid=$(/usr/bin/cd-discid | tr ' ' '-')

   if [[ ! -d "$CDLIBRARY/$cdid" ]] ; then
      play=$(new_playlist)
      status=$?
      if (( status == 0 )); then 
         mkdir -p "$CDLIBRARY/$cdid"
         mv $play "$CDLIBRARY/$cdid/CDPlayer.m3u"
         chmod a+r "$CDLIBRARY/$cdid/CDPlayer.m3u" 
         echo "$CDLIBRARY/$cdid/CDPlayer.m3u"
         return 0
      fi

      echo $play
      return 2
   fi

   echo "$CDLIBRARY/$cdid/CDPlayer.m3u"
   return 0
}


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
cdplaylist=$(playlists)
status=$?

if (( status == 0 )); then
   cp $cdplaylist $CDPLAYLIST
else
   mv $cdplaylist $CDPLAYLIST
fi
chmod a+r $CDPLAYLIST

/usr/bin/mpc -q clear
/usr/bin/mpc -q load CDPlayer
/usr/bin/eject -x 2
/usr/bin/mpc -q play
