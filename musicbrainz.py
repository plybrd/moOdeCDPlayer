#!/usr/bin/python3

import libdiscid
import musicbrainzngs as mb
import requests
import json
from getpass import getpass

this_disc = libdiscid.read(libdiscid.default_device())
mb.set_useragent(app='get-contents', version='0.1')
#mb.auth(u=input('Musicbrainz username: '), p=getpass())

release = mb.get_releases_by_discid(this_disc.id,
                                    includes=['artists', 'recordings'])
if release.get('disc'):
   this_release=release['disc']['release-list'][0]
   title = this_release['title']
   artist = this_release['artist-credit'][0]['artist']['name']
 
   #if this_release['cover-art-archive']['artwork'] == 'true':
   #   url = 'http://coverartarchive.org/release/' + this_release['id']
   #   art = json.loads(requests.get(url, allow_redirects=True).content)
   #   for image in art['images']:
   #      if image['front'] == True:
   #         cover = requests.get(image['image'], 
   #                              allow_redirects=True)
   #         fname = '{0} - {1}.jpg'.format(artist, title)
   #         print('COVER="{}"'.format(fname))
   #         f = open(fname, 'wb')
   #         f.write(cover.content)
   #         f.close()
   #         break
 
   #print('TITLE="{}"'.format(title))
   #print('ARTIST="{}"'.format(artist))
   #print('YEAR="{}"'.format(this_release['date'].split('-')[0]))
   print("#EXTM3U\n")
   for medium in this_release['medium-list']:
      for disc in medium['disc-list']:
         if disc['id'] == this_disc.id:
            tracks=medium['track-list']
            for track in tracks:
               time = int(float(track['recording']['length'] if 'recording' in track and 'length' in track['recording'] 
                          else (track['track_or_recording_length'] if 'track_or_recording_length' in track 
                          else track['length'] if 'length' in track else 0))/1000.)
               time = -1 if time == 0 else time
               print('#EXTINF:{},{} - {}'.format(time,
                                                track['number'], 
                                                track['recording']['title']))
               print("#EXTART: {}".format(artist))
               print("#EXTALB: {} ({})".format(title,this_release['date'].split('-')[0]))
               print('cdda:///{}\n'.format(track['number']))
            break
