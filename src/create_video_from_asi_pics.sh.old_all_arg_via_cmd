#!/bin/bash -e

#./create_video_from_asi_pics.dh  -s 2024-01-16 -e 2024-01-16 -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -n "*11.jpg"
#./create_video_from_asi_pics.dh  -s 2024-05-01 -e 2024-05-06 -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -o "../out/\$(date -d \${my_date} '+/%Y/%m/%d/')"   -n "*11.jpg"
#./create_video_from_asi_pics.dh  -s 2024-05-01 -e 2024-05-02 -t "TROPOS ACTRIS Radiation Observatory" -u "\(TARO\)" -v "OSCM, Mindelo" -w "Capo Verde" -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -o "../out/\$(date -d \${my_date} '+/%Y/%m/%d/')"   -n "*11.jpg"


startdate=$(date +%Y-%m-%d)
enddate=$startdate
directory_in="/mydirectory/"
directory_out="/mydirectory/"
name="*.jpg"
t="Institution/Project"
u="Institution/Project"
v="Location1"
w="Location2"

display_usage() { 
    echo "##############################################################################"
    echo "### The script creates a video from pics in a directory" 
    echo "###"
    echo "### Assumption 1: ffmpeg is installed"
    echo "### Assumption 2: pic files are jpeg"
    echo "##############################################################################"
}

# Extract Options
# ===============
while getopts ":s:e:d:n:o:t:u:v:w:h" optval "$@"
    do
        case $optval in
            "s") # 
                startdate="$OPTARG"
                ;;
            "e") # YYYYMMDD
                enddate="$OPTARG"
                ;;
            "d") # 
                directory_in="$OPTARG"
                ;;
            "n") # 
                name="$OPTARG"
                ;;
            "o") # 
                directory_out="$OPTARG"
                ;;
            "t") # 
                t="$OPTARG"
                ;;
            "u") # 
                u="$OPTARG"
                ;;
            "v") # 
                v="$OPTARG"
                ;;
            "w") # 
                w="$OPTARG"
                ;;
            "h")
                # help message
                display_usage
                echo ""
                echo "USAGE: $0  [options]"
                echo ""
                echo create_video_from_asi_pics.dh  -s 2024-01-14 -e 2024-01-16 -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -n "*11.jpg" -u "TROPOS TARO" -v "Capo Verde" -w "Mindelo OSCM"
                echo ""
                echo "OPTIONS:"
                echo "  -s <startdate>    string = 2023-01-22"
                echo "  -e <enddate>      string = 2024-11-30"
                echo "  -d <directory_in> string = rule to create subpath, default \"\\\${yyyy}/\\\${mm}/\\\${dd}\""
                echo "  -n <name>         string = part of file name"
                echo "  -o <directory_out>string = rule to create subpath, default \"\\\${yyyy}/\\\${mm}/\\\${dd}\""
                echo "  -t <u>            string = Institution/Project, eg: TROPOS ACTRIS Radiation Observatory (TARO)"
                echo "  -u <u>            string = Institution/Project, eg: (TARO)"
                echo "  -v <v>            string = Location name1, eg: Capo Verde"
                echo "  -w <w>            string = Location name2, eg: Mindelo OSCM"
                echo "  -h               Print help message and exit"
    
                exit

                ;;

            "?")
                echo "Unknown option $OPTARG"
                ;;
            :  )
                echo "Missing option argument for -$OPTARG" >&2; exit 1
                ;;
            *)
                errormsg="Unknown parameter or option error with option - $OPTARG"
                echo $errormsg
                ;;
    esac
done


if [[ $startdate -lt $enddate ]]; then
    echo "Error: startdate $startdate is taller than enddate $enddate"
    exit 1
fi

if [[ $directory_in == $directory_out ]]; then
    echo "Error: directory_in and directory_out are equal!!??"
    exit 1
fi

echo $directory


my_loop () {
    # get args
    my_date=$1
    directory_in=$2
    name=$3

    full_directory_in=$(eval echo "$directory_in")
    full_directory_out=$(eval echo "$directory_out")
      
    echo $full_directory_out
      
    # check if directory exists
    if [[ ! -d ${full_directory_in} ]]; then
        echo "Warning: directory_in not exists: ${full_directory_in}"
    else
        number_of_files=$(find ${full_directory_in} -maxdepth 1 -name "${name}" -printf 1 | wc -c)
  
        if [[ $number_of_files -lt 2 ]]; then
            echo "Warning: no files found at: ${full_directory_in}"
      
        else
            # create subdir
            if [[ ! -d ${full_directory_out} ]]; then
                echo "INFO: directory_out not exists: ${full_directory_out}"
                mkdir -p ${full_directory_out}
                echo "INFO: directory_out created: ${full_directory_out}"
            fi
    
        video_filename="${full_directory_out}${my_date}.mp4"
      
        cat $(find ${full_directory_in} -maxdepth 1 -name "${name}" | sort -V) | \
        #ffmpeg -framerate 20 -i - -vcodec libx264 -filter_complex "\
        #drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$u':fontsize=50:fontcolor=white:x=10:y=65,\
        #drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf':text='$v':fontsize=35:fontcolor=white:x=10:y=125,\
        #drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf':text='$w':fontsize=35:fontcolor=white:x=10:y=170,\
        #fade=type=in:duration=2:start_time=0,\
        #scale=720:-1" $video_filename
        
        
        ffmpeg -framerate 20 -i - -vcodec libx264 -filter_complex "\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$t':fontsize=36:fontcolor=white:x=10:y=51,\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$u':fontsize=36:fontcolor=white:x=10:y=100,\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf':text='$v':fontsize=35:fontcolor=white:x=1620:y=51,\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$w':fontsize=36:fontcolor=white:x=1620:y=100,\
        fade=type=in:duration=2:start_time=0,\
        scale=720:-1" $video_filename
        fi
    fi
  
  
  
}

while ! [[ $startdate > $enddate ]]; do
    echo $startdate
    
    my_loop $startdate "$directory_in" $name
    
    startdate=$(date -d "$startdate + 1 day" +%F)
done



#cat $(find /data/level0/all_sky_imager/asi16_oscm/2024/01/14/ -maxdepth 1 -name "*_11.jpg" | sort -V) | ffmpeg -framerate 20 -i - -vcodec libx264 -filter_complex "drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='TROPOS TARO':fontsize=50:fontcolor=white:x=10:y=65,\
#drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf':text='Cabo Verde, Mindelo, OSCM':fontsize=35:fontcolor=white:x=10:y=125,\
#fade=type=in:duration=2:start_time=0,\
#scale=720:-1" outputq2.mp4 
