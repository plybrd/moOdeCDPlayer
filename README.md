# moOde CD play

This repo contains code to add a CD playback function to the Raspberry Pi-based moOde music player.

The code assumes that a CD drive suitable for audio playback is already connected to the Raspberry Pi hosting the moOde player and is recognized by Raspbian as device /dev/cdrom.
 
## History

This work began as a contribution to the moOde project from Ashley Cox, communicated in email correspondence in the summer of 2019 with Tim Curtis and Kent Reed (TheOldPresbyope). That contribution subsequently has been modified and extended by Kent Reed. In his emails, Cox granted the moOde project full permission to use his contribution. An MIT license is used in this repo to grant explicitly this permission by both authors to all users. It is believed to be compatible with the GPL license used in the moOde codebase.

Similar work is described in https://github.com/TongboZhang/Moode_Extension. See additional links there.

## Design Intent

We intend the moOde CD playback function to mimic the behavior of a standalone CD player.

When an audio CD is inserted in the drive, moOde playback stops, the moOde queue is cleared and then loaded with a track list corresponding to the audio tracks on the CD. The user can play the tracks in the normal way. When the CD is ejected, playback stops and the queue is cleared. In particular, moOde retains no memory of the CD or its tracks. Saving a track as a favorite or setting it for clock radio will lead to an error later when moOde attempts to play it.

## Responsiveness

An optical CD drive is very slow compared to other storage devices. Then, too, nature of the CDDA (compact disk digital audio) encoding complicates finding and extracting an audio track from the CD. In addition, there is internal buffering involved.

Some sample timings (expect variability):

- Load a CD and display the track list: 12s
- Select track 1 and begin playing: 14s
- Change from track to track: 3s
- Return to track 1 from track 7: 10s

Moving backwards and forwards within a track also takes time.

The moOde time dial reading is suspect while these actions are occurring.

Once extracted, on the other hand, an audio CD track is played back at 44.1KHz/16bit just as if it were decoded from, say, a FLAC-encoded file.

## Planned Evolution of Releases

In Version 0 (the current release), the CD track list consists of primitive "cdda:///1", cdda:///2", etc., entries. The default moOde logo is displayed for all tracks, and, for each track played, the information displayed below the logo is an ugly "File does not exist" and "Unknown artist - Unknown album"

Version 1 (in progress), is a prettified Version 0. The track list consists of "CD Track 1", "CD Track 2", etc., entries. A CDDA logo is displayed for all tracks, and the information displayed below the logo is sanitized.

In Version 2 (still a pipe dream), external data services are queried to obtain actual track information and CD coverart. Given the current state of these data services, the results may be reasonably good for some genres and hit-or-miss for others.

## Installation

The Version 0 code is contained in two simple scripts, two corresponding systemd services files, and a udev ruleset.

The simplest method of installation is to click the green github "Clone or download" button and then click the "Download ZIP" button which appears. The zip file moOdeCDPlay-master.zip will be offered for download to your local host. 

1. Download and transfer this file to the /home/pi directory in the target moOde player
2. On the target moOde player, go to the /home/pi directory and unzip the file
3. Change to the /home/pi/moOdeCDPlayer-master directory which has been created
4. Execute the command
```
/bin/bash install.sh
```
Alternatively, mark the script executable and...well...you know the drill

5. Once the script finishes successfully, you should reboot. At this point the moOde CD playback function should be working and you can delete both moOdeCDPlay-master.zip and the moOdeCDPlay-master directory.

Good listening!
