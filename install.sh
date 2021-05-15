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
                    python3-mpd \
                    swig \
                    abcde

sudo pip3 install pycdio

sudo cp addaudiocd.sh /usr/local/bin/addaudiocd.sh
sudo cp remaudiocd.sh /usr/local/bin/remaudiocd.sh
sudo cp moodecdplay.py /usr/local/bin/moodecdplay.py
sudo cp addaudiocd.service /etc/systemd/system/addaudiocd.service
sudo cp remaudiocd.service /etc/systemd/system/remaudiocd.service
sudo cp 99-srX.rules /etc/udev/rules.d/99-srX.rules
sudo chmod +x /usr/local/bin/addaudiocd.sh
sudo chmod +x /usr/local/bin/remaudiocd.sh
sudo chmod +x /usr/local/bin/moodecdplay.py
echo "Done - please reboot moOde to complete installation."
