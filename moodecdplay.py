#!/usr/bin/python3

import libdiscid
import pycdio
import cdio
import musicbrainzngs as mb
import mpd

import unicodedata
import re
import pathlib
import itertools
import json

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class NotCDDAError(Error):
    """Error raised if the inserted CD is not an audio CD."""
    pass



def hex_cdid(disc) :
    """
    returns the CD as an hexadecimal string.
    """
    hexa = [hex(ord(i)).lstrip("0x").rstrip("L") 
                for i in disc.id
           ]
    return '-'.join(i+j for i,j in zip(hexa[0::2],hexa[1::2]))

def cache_dir(disc):
    """
    Build the Path object pointing to the cache directory
    corresponding to this disc.
    """
    cd_library = pathlib.Path("/var/lib/moode_cd_library")
    if not cd_library.exists():
            cd_library.mkdir()
    p = pathlib.Path(cd_library, hex_cdid(disc))
    return p

def cache_info(disc):
    p = cache_dir(disc)
    p = pathlib.Path(p,"cd_info.json")
    return p

def read_cached_info(disc):
    json_file = cache_info(disc)
    if json_file.exists():
        metadata = json.load(json_file.open(mode="rt"))
    else:
        metadata = None
    return metadata

def write_info_in_cache(disc,metadata):
    directory = cache_dir(disc)
    try:
        if not directory.exists():
            directory.mkdir()
        json_file = cache_info(disc)

        with json_file.open(mode="wt") as f:
            json.dump(metadata,f)
    except Exception as e:
        print(e)

def itrack(disc):
    return (str(i) for i in range(disc.first_track,disc.last_track))

def info_from_cdtext(disc):
    try:
        d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
    except IOError as err:
        print("Problem finding a CD-ROM")
        raise err

    if d.get_disc_mode() != 'CD-DA':
        raise NotCDDAError()

    t = d.get_cdtext()

    # Build the dictionnary for album info 
    album_info = {pycdio.cdtext_field2str(i):t.get(i,0) 
                    for i in range(pycdio.MIN_CDTEXT_FIELD,
                                   pycdio.MAX_CDTEXT_FIELDS) 
                        if t.get(i,0) is not None}

    if "TITLE" in album_info:
        disc_info = {"album" : album_info["TITLE"]}

        if "PERFORMER" in album_info:
            disc_info["albumartist"]=album_info["PERFORMER"]
        elif "COMPOSER" in album_info:
            disc_info["albumartist"]=album_info["COMPOSER"]
        elif "SONGWRITER" in album_info:
            disc_info["albumartist"]=album_info["SONGWRITER"]
    else:
        return None

    disc_info["tracks"] = {}
    tracks_info = disc_info["tracks"]

    for track in itrack(disc):
        track_info = {pycdio.cdtext_field2str(i):t.get(i,int(track)) 
                        for i in range(pycdio.MIN_CDTEXT_FIELD,
                                   pycdio.MAX_CDTEXT_FIELDS) 
                            if t.get(i,int(track)) is not None}   

        tracks_info[track] = {"track" : track,
                              "album" : disc_info["album"],
                              "name"  : "Track {}".format(track),
                              "title" : track_info["TITLE"] if "TITLE" in track_info else "Unkown"
                             }
        
        if "GENRE" in track_info:
            tracks_info[track]["genre"] = track_info["GENRE"]

        if "COMPOSER" in track_info:
            tracks_info[track]["composer"] = track_info["COMPOSER"]

        if "ARRANGER" in track_info:
            tracks_info[track]["conductor"] = track_info["ARRANGER"]

        if "PERFORMER" in track_info:
            tracks_info[track]["artist"] = track_info["PERFORMER"]
        elif "SONGWRITER" in track_info:
            tracks_info[track]["artist"] = track_info["SONGWRITER"]
        elif "COMPOSER" in track_info:
            tracks_info[track]["artist"] = track_info["COMPOSER"]
        else:
            tracks_info[track]["artist"] = "Unkown"
                                    

    return disc_info

def info_from_musicbrainz(disc):
    mb.set_useragent(app='get-contents', version='0.1')
    release = mb.get_releases_by_discid(disc.id,
                                        includes=['artists', 'recordings'])

    if release.get('disc'):
        this_release=release['disc']['release-list'][0]
        title = this_release['title']
        artist = this_release['artist-credit'][0]['artist']['name']

        metadata = {"album"       : title,
                     "albumartist" : artist,
                     "tracks"      : {}
                    }

        tracks_info = metadata["tracks"]

        for medium in this_release['medium-list']:
            for this_disc in medium['disc-list']:
                if this_disc['id'] == disc.id:
                    tracks=medium['track-list']
                    for track in tracks:
                        tracks_info[track['number']] = {
                              "track" : track['number'],   
                              "artist": metadata["albumartist"],
                              "album" : metadata["album"],
                              "name"  : "Track {}".format(track['number']),
                              "title" : track['recording']['title'],
                              "date"  : this_release['date'].split('-')[0]
                         }
                        
                    break

    else:
        metadata = None
    
    return metadata

def info_default(disc):
    metadata = {"album"       : "Unkown",
                "albumartist" : "Unkown",
                "tracks"      : {}
               }
    
    tracks_info = metadata["tracks"]
    
    for track in itrack(disc):
        tracks_info[i] = {"track" : id,   
                          "artist": "Unkown",
                          "album" : "Unkown",
                          "name"  : "Track {}".format(track['number']),
                          "title" : "Track {}".format(track['number'])
                         }

    return metadata

def build_info(disc):
    
    metadata = info_from_cdtext(disc)
    if metadata is None:
        metadata = info_from_musicbrainz(disc)

    if metadata is not None:
        write_info_in_cache(disc,metadata)
    else:
        metadata = info_default(disc)

    return metadata


def cd_info(disc):

    metadata = read_cached_info(disc)
    if metadata is None:
        metadata = build_info(disc)

    return metadata

def eventually_mpd_connect(mpd,host="localhost", port=6600):
    try:
        mpd.connect(host,port)
    except:
        pass


def md_push_disc(disc, autoplay=True, host="localhost", port=6600):
    m = mpd.MPDClient()

    eventually_mpd_connect(m,host,port)
    m.clear()
    track_ids = {i : m.addid("cdda:///{}".format(i))
                  for i in itrack(disc)
                }

    if autoplay:
        eventually_mpd_connect(m,host,port)
        m.single(0)
        m.repeat(0)
        m.play()

    metadata = cd_info(disc)

    if metadata is not None:
        eventually_mpd_connect(m,host,port)
        for i in itrack(disc):
            for k in metadata["tracks"][i]:
                m.addtagid(track_ids[i],k,metadata["tracks"][i][k])
            



    



if __name__ == "__main__" :

    disc = libdiscid.read(libdiscid.default_device())
    md_push_disc(disc)

