#!/usr/bin/awk -f

function seconde(t) {
    split(t,tp,":")
    return tp[1]*60+tp[2] 
}

BEGIN {
    track_list_on=0
    cd_report = 0
    cd_text = 0
    title_ok = 2
}

/^Disc mode is listed as:/ {
    if ($NF != "CD-DA")
        exit 1;
}

/^CD-ROM Track List/ {
    track_min = int(substr($(NF-2),2));
    track_max = int(substr($NF,1,length($NF)-1));
}

(track_list_on) {
    track_current=$1;
    sub(":$","",track_current);
    track_current = int(track_current)

    track_starts[track_current]=seconde($2);

    if (track_current > track_max) {
        track_list_on = 0;
        last_time = track_starts[track_current];
        for (i=track_min; i <= track_max; i++) {
            if (i < track_max) 
                track_end = track_starts[i+1];
            else
                track_end = last_time;
            track_duration[i] = track_end - track_starts[i];
            track_title[i] = sprintf("CD Track %3d",i);
        }
    }
}

(cd_text && $0 ~ /CD-TEXT for Track/) {
    track_current=$NF;
    sub(":$","",track_current);
    track_current = int(track_current)
}

(cd_text && $1 == "TITLE:") {
    $1="";
    sub("^  *","",$0)
    track_title[track_current] = $0
    title_ok = 0
}

( cd_text && $1 == "Language") {
  cd_text = 0
  cd_report = 0
}

(cd_report && $1 == "Language") {
  cd_text = 1
}

/CD Analysis Report/ {
    cd_report = 1
}

/#: MSF/ {
    track_list_on=1
} 

END {
    print "#EXTM3U";
    print "";
    for (i=track_min; i <= track_max; i++) {
        print "#EXTINF:" track_duration[i] "," track_title[i];
        print "cdda:///" i;
        print "";
    }

    exit title_ok
}