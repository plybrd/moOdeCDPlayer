# moOde CD play

This repo contains code to add a CD playback function to the Raspberry Pi-based moOde audio player (http://moodeaudio.org).

The code assumes that a CD drive suitable for audio playback is already connected to the Raspberry Pi hosting the moOde player and is recognized by Raspbian as device /dev/cdrom.

## Status

On May the 14th, I restarted to develop that small project that was sleeping since a year.

## History

This work began as a contribution to the moOde project from Ashley Cox (https://ashleycox.co.uk/), communicated in email correspondence in the summer of 2019 with Tim Curtis (moOde maintainer) and Kent Reed (TheOldPresbyope). That contribution subsequently has been modified and extended by Kent Reed. In his emails, Cox granted the moOde project full permission to use his contribution. An MIT license is used in this repo to grant explicitly this permission by both authors to all users. It is believed to be compatible with the GPL license used in the moOde codebase.

Similar work is described in https://github.com/TongboZhang/Moode_Extension. See additional links there.

On May the 14th I forked the project maintained by [TheOldPresbyope](https://github.com/TheOldPresbyope) and started to redevelop the code of the two main scripts and add few other pieces of code.

## Design Intent

We intend the moOde CD playback function to mimic the behavior of a standalone CD player.

When an audio CD is inserted in the drive, the new CD is inspected and a playlist is built from its content.
The moOde playback stops, the moOde queue is cleared and then the playlist is loaded and played. 
When the CD is ejected, using the manual eject button on the drive, playback stops and the playlist and the queue are cleared. 
In particular, moOde retains no memory of the CD or its tracks. Saving a track as a favorite or setting it for clock radio 
will lead to an error later when moOde attempts to play it. Nevertheless the generated playlist is saved in a cache directory
and can be quickly copied for a new use if the CD is inserted again later on.

## Responsiveness

An optical CD drive is very slow compared to other storage devices. Then, too, the nature of the CDDA (compact disk digital audio) encoding complicates retrieving audio tracks from the CD. In addition, there is internal buffering involved.

Some sample timings (expect variations with different hardware):

- Load a CD and display the track list: 12s
- Select track 1 and begin playing: 14s
- Change from track to track: 3s
- Return to track 1 from track 7: 10s

Moving backwards and forwards within a track also takes time.

The moOde time dial reading is suspect while these actions are occurring.

Once extracted, on the other hand, an audio CD track is played back at 44.1KHz/16bit just as if it were decoded from, say, a FLAC-encoded file.

## Planned Evolution of Releases

In Version 0 (the orginal release by [TheOldPresbyope](https://github.com/TheOldPresbyope)), the CD track list consists of primitive "cdda:///1", cdda:///2", etc., entries. 
The default moOde logo is displayed for all tracks, and, for each track played, the information displayed below the logo is an ugly 
"File does not exist" and "Unknown artist - Unknown album"

Version EC1 is able to extract the track metadata from the CD text or MusicBrainz. But the information displayed below the logo is still ugly.

My aim for the next version would be to display correctly information displayed below the logo and perhaps display the cover of the disk as logo when
available

## Installation

The Version 0 code is contained in two simple scripts, two corresponding systemd service files, and a udev ruleset.

The simplest method of installation is to click the green github "Clone or download" button and then click the "Download ZIP" button which appears. The zip file moOdeCDPlay-master.zip will be offered for download to your local host. 

1. Download and transfer this file to the /home/pi directory in the target moOde player
2. On the target moOde player, go to the /home/pi directory and unzip the file
3. Change to the /home/pi/moOdeCDPlay-master directory which has been created
4. Execute the command
`/bin/bash install.sh` or, alternatively, mark the script executable and...well...you know the drill

5. Once the script finishes successfully, you should reboot. At this point the moOde CD playback function should be working and you can delete both moOdeCDPlay-master.zip and the moOdeCDPlay-master directory.

Good listening!

## Odds and Ends

### Hardware

This code was developed on the following system
- moOde 7.2.1
- RPi3B
- DVD player : HL-DT-ST DVDRAM GT30N [purchased new on-line for less than 20€]. It is a bit too noisy

### SoX

A problem experienced in early testing with audible dropouts during CD playback was traced to SoX resampling at 32 bit/384KHz (inadvertently left on after a stress test of the RPi4B). Disabling resampling eliminated the dropouts. Your mileage with SoX resampling may vary.

