#!/bin/bash

echo "Install V-EC1 moOdeCDPlay files in moOde."

# moOdeCDPlay V0.1 script
if [ ! -f /var/www/command/moode.php ]; then
    echo
    echo "I'm sorry, Dave, I'm afraid I can't do that."
    echo "In case you didn't notice, this doesn't look like a moOde installation."
    exit 1
fi

sudo apt -y install libcdio-utils \
                    python3-musicbrainzngs \
                    python3-requests \
                    python3-libdiscid \
                    swig 

sudo pip3 install -U pycdio
sudo pip3 install -U python-mpd2
sudo cp addaudiocd.sh /usr/local/bin/addaudiocd.sh
sudo cp remaudiocd.sh /usr/local/bin/remaudiocd.sh
sudo cp moodecdplay.py /usr/local/bin/moodecdplay.py
sudo cp addaudiocd.service /etc/systemd/system/addaudiocd.service
sudo cp remaudiocd.service /etc/systemd/system/remaudiocd.service
sudo cp 99-srX.rules /etc/udev/rules.d/99-srX.rules
sudo chmod +x /usr/local/bin/addaudiocd.sh
sudo chmod +x /usr/local/bin/remaudiocd.sh
sudo chmod +x /usr/local/bin/moodecdplay.py

#if [[ ! -f /var/www/coverart.php.ori ]] ; then
#    sudo cp /var/www/coverart.php /var/www/coverart.php.ori
#fi
#sudo cp coverart.php /var/www/coverart.php

if [[ ! -f /var/www/inc/playerlib.php.ori ]] ; then
    sudo cp /var/www/inc/playerlib.php /var/www/inc/playerlib.php.ori
fi
sudo cp playerlib.php /var/www/inc/playerlib.php


sudo mkdir -p /var/lib/moode_cd_library/default_cd
sudo cp icon-cd-5.jpg /var/lib/moode_cd_library/default_cd/default_cd.jpg

echo "Done - please reboot moOde to complete installation."
