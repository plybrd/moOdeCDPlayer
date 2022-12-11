#!/bin/bash

echo "Install V0.3 moOdeCDPlay files in moOde."

if [ ! -x `which moodeutl` ]; then
    echo
    echo "I'm sorry, Dave, I'm afraid I can't do that."
    echo "In case you didn't notice, this doesn't look like a moOde installation."
    exit 1
fi

sudo cp moodecdplayer /usr/local/bin/moodecdplayer
sudo cp moodeengupdate /usr/local/bin/moodeengupdate
sudo cp audiocd@.service /etc/systemd/system/audiocd@.service
sudo cp 99-srX.rules /etc/udev/rules.d/99-srX.rules
sudo cp mpd.custom.conf /etc/mpd.custom.conf
sudo chmod +x /usr/local/bin/moodecdplayer
sudo chmod +x /usr/local/bin/moodeengupdate

udevadm control --reload
udevadm trigger

# Add feature 'Developer tweaks' to account for mpd.custom.conf
moodeutl -A add 32768

# Backup files have extension '.orig'
if [[ ! -f /var/www/inc/mpd.php.orig ]] ; then
    sudo patch -b /var/www/inc/mpd.php mpd.php.patch
fi
if [[ ! -f /var/www/command/queue.php.orig ]] ; then
    sudo patch -b /var/www/command/queue.php queue.php.patch
fi

sudo mkdir -p /var/lib/moode_cd_library/default_cd
sudo cp icon-cd-5.jpg /var/lib/moode_cd_library/default_cd/default_cd.jpg
# Eine kleine Bildvariante erstellen?
sudo ln /var/lib/moode_cd_library/default_cd/default_cd.jpg /var/lib/moode_cd_library/default_cd/default_cd_sm.jpg
sudo ln -s /var/lib/moode_cd_library/default_cd /var/local/www/imagesw/current_cd

echo "Done - please insert a CD."
