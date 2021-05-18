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
import os
import copy
import requests
import glob
import hashlib
import configparser
import optparse
import sys


##
## Default values
##

# The default place for the config file
DEFAULT_CONFIG = "/etc/moodecdplay.conf"

##
## List of the error code leading to an abortion of the process
##

# There is no audio CD in the player
NO_AUDIO_CD_ERROR = 1

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class NotCDDAError(Error):
    """Error raised if the inserted CD is not an audio CD."""
    pass


def read_config(options):

    __default__ ="""
    [On CD insertion]
    Autoplay = Yes
    Clear_queue = Yes

    [On CD ejection]
    Clear_queue = No

    [Metadata]
    Use_musicbrainz = Yes
    Cache_metadata = Yes
    """
    config = configparser.ConfigParser()
    config.read_string(__default__)
    configfile = pathlib.Path(options.configfile)
    if configfile.exists():
        config.read(configfile)
    return config


def current_disc():
    """
    Returns the disc information corresponding to the disc
    currently insterted into the default USB player.
    
    It contains among other data, the musicbrainz disc id
    and the number of tracks.
    """

    try:
        d = cdio.Device(driver_id=pycdio.DRIVER_UNKNOWN)
    except IOError as err:
        d = None

    if d is not None :
        try:
            if d.get_disc_mode() == 'CD-DA':
                d = libdiscid.read(libdiscid.default_device())
            else:
                d = None
        except :
            d = None

    return d


def hex_cdid(disc) :
    """
    returns the musicBrainz CD is as an hexadecimal string.

    The original code is taken by two letters and the ascii
    code of each letters is converted to hexadecimal.

    the original code : QMSaDuuKtKVWKD_cimSlvt2on5o-
    is converted into :
        514d-5361-4475-754b-744b-5657-4b44-5f63-696d-536c-7674-326f-6e35-6f2d

    That code is used to generate file names in moodecdplayer 
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

def moode_cd_dir(disc):
    return pathlib.Path("/var/local/www/imagesw/current_cd")

def default_cd_dir(disc):
    return pathlib.Path("/var/lib/moode_cd_library/default_cd")


def cache_info(disc):
    p = cache_dir(disc)
    p = pathlib.Path(p,"cd_info.json")
    return p

def cover_file(disc):
    p = cache_dir(disc)
    p = pathlib.Path(p,hex_cdid(disc) + ".jpg")
    return p

def theme_jpg_file(disc):
    filename = hashlib.md5(b"cdda://").hexdigest() + ".jpg"
    return pathlib.Path("/var/local/www/imagesw/thmcache",filename)

def theme_sm_jpg_file(disc):
    filename = hashlib.md5(b"cdda://").hexdigest() + "_sm.jpg"
    return pathlib.Path("/var/local/www/imagesw/thmcache",filename)



def read_cached_info(disc):
    json_file = cache_info(disc)
    if json_file.exists():
        metadata = json.load(json_file.open(mode="rt"))
    else:
        metadata = None
    return metadata

def write_info_in_cache(disc,metadata):
    if metadata['source'] != 'default':
        directory = cache_dir(disc)
        try:
            if not directory.exists():
                directory.mkdir()
            json_file = cache_info(disc)

            with json_file.open(mode="wt") as f:
                json.dump(metadata,f)
        except Exception as e:
            print(e)

def is_cached_metadata(disc):
    return cache_info(disc).exists()

def itrack(disc):
    return (str(i) for i in range(disc.first_track,disc.last_track+1))



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
        disc_info = {"source" : "CDText",
                     "album" : album_info["TITLE"]
                    }

        if "PERFORMER" in album_info:
            disc_info["albumartist"]=album_info["PERFORMER"]
        elif "COMPOSER" in album_info:
            disc_info["albumartist"]=album_info["COMPOSER"]
        elif "SONGWRITER" in album_info:
            disc_info["albumartist"]=album_info["SONGWRITER"]
    else:
        return None

    disc_info["discid"] = disc.id

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
                              "title" : track_info["TITLE"] if "TITLE" in track_info else "Unknown"
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
            tracks_info[track]["artist"] = "Unknown"
                                    

    return disc_info

def get_musicbrainz_release(disc):
    mb.set_useragent(app='get-contents', version='0.1')

    try:
        release = mb.get_releases_by_discid(disc.id,
                                            includes=['artists', 'recordings'])
    except mb.ResponseError:
        release = None

    if release is not None and "disc" in release:
        this_release=release['disc']['release-list'][0]
    else:
        this_release=None
 
    return this_release

def save_musicbrainz_cover(disc,release):
    saved = False

    if release['cover-art-archive']['artwork'] == 'true':
        url = 'http://coverartarchive.org/release/' + release['id']
        art = json.loads(requests.get(url, allow_redirects=True).content)

        for image in art['images']:
            if image['front'] == True:
                cover = requests.get(image['image'], 
                                        allow_redirects=True)

                directory = cache_dir(disc)
                try:
                    if not directory.exists():
                        directory.mkdir()
                    filename=cover_file(disc)
                    with filename.open(mode='wb') as f:
                        f.write(cover.content)
                        f.close()
                        saved = True
                except:
                    pass
                break

    return saved



def get_cover(disc, only_from_cache=False):
    filename=cover_file(disc)

    if filename.exists():
        return filename

    if not only_from_cache:
        release = get_musicbrainz_release(disc)
        if release is not None and save_musicbrainz_cover(disc,release):
            return filename

    return None

def install_cover(disc, only_from_cache=False):
    """
    Installs the symbolic links in the moOde directories
    making the cover arts accessible for the web site.
    """

    cover = get_cover(disc,only_from_cache)
    dest  = moode_cd_dir(disc)

    if cover is not None:
        source = cache_dir(disc)
    else:
        source = default_cd_dir(disc)
       
    if dest.is_symlink() :
        dest.unlink()
    dest.symlink_to(source)

    theme_jpg = theme_jpg_file(disc)
    if theme_jpg.is_symlink() :
        theme_jpg.unlink()
    theme_jpg.symlink_to(list(dest.glob("*.jpg"))[0])

    theme_sm_jpg = theme_sm_jpg_file(disc)
    if theme_sm_jpg.is_symlink() :
        theme_sm_jpg.unlink()
    theme_sm_jpg.symlink_to(list(dest.glob("*.jpg"))[0])

def uninstall_cover(disc):
    """
    Removes the symbolic links in the moOde directories
    making the cover arts accessible for the web site.
    """
    if moode_cd_dir(disc).is_symlink():
        moode_cd_dir(disc).unlink()

    if theme_jpg_file(disc).is_symlink():
        theme_jpg_file(disc).unlink()

    if theme_sm_jpg_file(disc).is_symlink():
        theme_sm_jpg_file(disc).unlink()



def info_from_musicbrainz(disc):
    this_release = get_musicbrainz_release(disc)

    if this_release is not None:
        title = this_release['title']
        artist = this_release['artist-credit'][0]['artist']['name']


        metadata = {"source" : "musicbrainz",
                     "album"       : title,
                     "albumartist" : artist,
                     "discid"      : disc.id,
                     "tracks"      : {}
                    }

        tracks_info = metadata["tracks"]

        # album,genre,track,disc,date,composer,conductor,performer,encoded

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

        save_musicbrainz_cover(disc,this_release)        

    else:
        metadata = None
    
    return metadata

def info_default(disc):
    metadata = {"source"      : "default",
                "album"       : "Unknown",
                "albumartist" : "Unknown",
                "discid"      : disc.id,
                "tracks"      : {}
               }
    
    tracks_info = metadata["tracks"]
    
    for track in itrack(disc):
        tracks_info[track] = {
                          "track" : track,   
                          "artist": "Unknown",
                          "album" : "Unknown",
                          "name"  : "Track {}".format(track),
                          "title" : "Track {}".format(track)
                         }

    return metadata


def cd_info(disc):

    metadata = read_cached_info(disc)
    if metadata is None:
        metadata = build_info(disc)

    return metadata

def fast_info(disc):
    metadata = read_cached_info(disc)
    method = "cached"
    if metadata is None:
        metadata = info_from_cdtext(disc)
        method = "cdtext"
    if metadata is None:
        metadata = info_default(disc)
        method = "default"
    return method,metadata

def dict_diff(old,new,excepted=[]):
    updated = {}
    for k in new:
        if k not in excepted:
            if k in old:
                if type(old[k]) == dict and type(new[k]) == dict:
                    up_k = dict_diff(old[k],new[k],excepted)
                    if (len(up_k) > 0):
                        updated[k] = up_k
                elif new[k]!=old[k]:
                    updated[k] = new[k]

    return updated

def update_with_musicbrainz(disc,metadata):
    """
    Updates the metadata structure with data from musicbrainz
    and returns the dict of modified values.
    The metadata input dictionnary is potentially modified.
    """
    # Save the orginal metadata
    metadata_old = copy.deepcopy(metadata)

    # load the metadata from musicmrainz
    mb_metadata = info_from_musicbrainz(disc)

    # musicmrainz returns metadata update the old ones.
    if mb_metadata is not None:
        metadata.update(mb_metadata)

        # Looks for updated metadata
        updated=dict_diff(metadata_old,metadata, excepted=["source"])

        # if we update nothing except the source them
        # switch back the source
        if len(updated) == 0:
            metadata["source"] = metadata_old["source"]
        else:
            updated["source"] = metadata["source"]
    else:
        updated = {}

    # returns the list of updated field
    return updated


def metadata_source(metadata):
    return metadata["source"]

def eventually_mpd_connect(mpd,host="localhost", port=6600):
    try:
        mpd.connect(host,port)
    except:
        pass

def mpd_queue_info(host="localhost", port=6600):
    """
    Returns the list of the CD tracks present in the MPD queue.
    """
    m = mpd.MPDClient()

    error=True
    while(error):
        error = False
        eventually_mpd_connect(m,host,port)
        try:
            info = {s["file"].split("/")[-1] : s 
                     for s in m.playlistinfo()
                     if s['file'][0:8]=="cdda:///"}
        except mpd.ConnectionError:
            error=True
    
    return info

def mpd_clear_cd_tracks(host="localhost", port=6600):
    """
    Remove every CD tracks from the MPD queue

    If one of the CD tracks was playing then a STOP command
    is sent before deleting the tracks.
    """
    m = mpd.MPDClient()
    eventually_mpd_connect(m,host,port)

    current_info = mpd_queue_info(host,port)

    cdtracks = [current_info[k]['id'] 
                    for k in current_info]

    cs = m.currentsong()

    if "id" in cs and cs['id'] in cdtracks:
        m.stop()

    m.command_list_ok_begin()
    for k in cdtracks:
        m.deleteid(int(k))
    m.command_list_end()



def mpd_load_disc(disc, autoplay=True, host="localhost", port=6600):

    # Load metadata that can be loaded quickly
    method,metadata = fast_info(disc)

    # save the metadata if they are not feteched from cache
    if method != "cached":
        write_info_in_cache(disc,metadata)

    install_cover(disc, only_from_cache=True)

    m = mpd.MPDClient()
    eventually_mpd_connect(m,host,port)


    # Sends the disc tracks to MPD
    m.clear()
    track_ids = {i : m.addid("cdda:///{}".format(i))
                  for i in itrack(disc)
                }

    m.command_list_ok_begin()
    # And annote the track with the first set of metadata
    for i in metadata["tracks"]:
        for k in metadata["tracks"][i]:
           m.addtagid(track_ids[i],k,metadata["tracks"][i][k])

    m.command_list_end()

    # If in autoplay mode launch the playlist
    if autoplay:
        eventually_mpd_connect(m,host,port)
        m.single(0)
        m.repeat(0)
        m.play()


    # Check for update of the musicbrainz data
    updated = update_with_musicbrainz(disc,metadata)
    install_cover(disc, only_from_cache=False)

    eventually_mpd_connect(m,host,port)
    current_info = {s["track"]:s for s in m.playlistinfo()}

    m.command_list_ok_begin()
    
    for i in metadata["tracks"]:
        current = current_info[i]
        for k in metadata["tracks"][i]:
            if k in current:
                m.cleartagid(track_ids[i],k)
            m.addtagid(track_ids[i],k,metadata["tracks"][i][k])
        
    m.command_list_end()

    if updated:
        write_info_in_cache(disc,metadata)
        # if "tracks" in updated:


        #     current_info = {s["track"]:s for s in m.playlistinfo()}

        #     m.command_list_ok_begin()

        #     for i in updated["tracks"]:
        #         current = current_info[i]
        #         for k in updated["tracks"][i]:
        #             if k in current:
        #                 m.cleartagid(track_ids[i],k)
        #             m.addtagid(track_ids[i],k,updated["tracks"][i][k])

        #     m.command_list_end()

        # saved the updated version of metadata





def on_insert(disc, host="localhost", port=6600):
    mpd_load_disc(disc,port)

def on_eject(disc, host="localhost", port=6600):
    mpd_clear_cd_tracks(host,port)
    uninstall_cover(disc)

def save_config(disc, host="localhost", port=6600):
    pass




    

if __name__ == "__main__" :

    ##
    ## Declares the script options
    ##

    option_parser = optparse.OptionParser()
    option_parser.add_option("-c", "--config", 
                             dest="configfile",
                             help="location of the configuration file", 
                             metavar="FILE",
                             default=DEFAULT_CONFIG)


    ##
    ## Inserts every options corresponding to the command to execute
    ##

    #--> The On eject command

    option_parser.add_option("-e", "--on-eject", 
                             dest="action",
                             action="store_const",
                             const=on_eject,
                             help="To run the actions to be done on CD eject", 
                             default=on_insert)

    #--> The On insert command

    option_parser.add_option("-i", "--on-insert", 
                             dest="action",
                             action="store_const",
                             const=on_insert,
                             help="To run the actions to be done on CD insertion", 
                             default=on_insert)

    #--> The Save config command

    option_parser.add_option("-s", "--save-config", 
                             dest="action",
                             action="store_const",
                             const=save_config,
                             help="Save the default version of the config file", 
                             default=on_insert)


    (options, args) = option_parser.parse_args()


    ##
    ## Check that an Audio CD is inserted into the default player 
    ##

    disc = current_disc()
    if disc is None:
        print("No Audio CD in the drive", file=sys.stderr,flush=True)



    config = read_config(options)

    options.action(disc,host="localhost",port=6600)

    if disc is None:
        sys.exit(NO_AUDIO_CD_ERROR)
