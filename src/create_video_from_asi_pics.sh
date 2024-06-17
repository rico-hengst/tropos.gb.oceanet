#!/bin/bash -e

#./create_video_from_asi_pics.dh  -s 2024-01-16 -e 2024-01-16 -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -n "*11.jpg"
#./create_video_from_asi_pics.dh  -s 2024-05-01 -e 2024-05-06 -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -o "../out/\$(date -d \${my_date} '+/%Y/%m/%d/')"   -n "*11.jpg"
#./create_video_from_asi_pics.dh  -s 2024-05-01 -e 2024-05-02 -t "TROPOS ACTRIS Radiation Observatory" -u "\(TARO\)" -v "OSCM, Mindelo" -w "Capo Verde" -d "/data/level0/all_sky_imager/asi16_oscm/\$(date -d \${my_date} '+/%Y/%m/%d/')" -o "../out/\$(date -d \${my_date} '+/%Y/%m/%d/')"   -n "*11.jpg"
#./create_video_from_asi_pics.sh -s 2019-12-12 -e 2019-12-12 -c pic2video.config

# set/get default 
CONFIG_FILE="../conf/pic2video.config"

echo $CONFIG_FILE

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
while getopts ":s:e:c:h" optval "$@"
    do
        case $optval in
            "s") # 
                START_DATE="$OPTARG"
                ;;
            "e") # YYYYMMDD
                END_DATE="$OPTARG"
                ;;
            "c") # 
                CONFIG_FILE="$OPTARG"
                ;;
            "h")
                # help message
                display_usage
                echo ""
                echo "USAGE: $0  [options]"
                echo ""
                echo create_video_from_asi_pics.dh  -s 2024-01-14 -e 2024-01-16 -c "config_file"
                echo ""
                echo "OPTIONS:"
                echo "  -s <START_DATE>   string = 2023-01-22"
                echo "  -e <END_DATE>     string = 2024-11-30"
                echo "  -c <CONFIG_FILE>  string = relativ path to current script"
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



# check
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Error: configfile not exists: $CONFIG_FILE"
  exit 1
fi

# check if DATES are provided, otherwise get from config
if [[ -z "$START_DATE" || -z "$END_DATE" ]]
then
    echo "START_DATE or STOP_DATE are not provided"
    echo "Get START_DATE, END_DATE from config"
    START_DATE=$(grep -Po "START_DATE=\K.*" "pic2video.config" || true); # echo 4: $START_DATE
    START_DATE=$(eval echo "$START_DATE"); # echo 4: $START_DATE

    END_DATE=$START_DATE
fi

# get config

DIRECTORY_IN=$(grep -Po "DIRECTORY_IN=\K.*" "$CONFIG_FILE" || true)
DIRECTORY_IN=$(eval echo "$DIRECTORY_IN")

DIRECTORY_OUT=$(grep -Po "DIRECTORY_OUT=\K.*" "$CONFIG_FILE" || true)
DIRECTORY_OUT=$(eval echo "$DIRECTORY_OUT")

FILENAME_IN_PATTERN=$(grep -Po "FILENAME_IN_PATTERN=\K.*" "$CONFIG_FILE" || true)
FILENAME_IN_PATTERN=$(eval echo "$FILENAME_IN_PATTERN")

FILENAME_OUT_PATTERN=$(grep -Po "FILENAME_OUT_PATTERN=\K.*" "$CONFIG_FILE" || true)
FILENAME_OUT_PATTERN=$(eval echo "$FILENAME_OUT_PATTERN")

INSTITUTION_PROJECT_1=$(grep -Po "INSTITUTION_PROJECT_1=\K.*" "$CONFIG_FILE" || true)
INSTITUTION_PROJECT_1=$(eval echo "$INSTITUTION_PROJECT_1")

INSTITUTION_PROJECT_2=$(grep -Po "INSTITUTION_PROJECT_2=\K.*" "$CONFIG_FILE" || true)
INSTITUTION_PROJECT_2=$(eval echo "$INSTITUTION_PROJECT_2")

LOCATION_1=$(grep -Po "LOCATION_1=\K.*" "$CONFIG_FILE" || true)
LOCATION_1=$(eval echo "$LOCATION_1")

LOCATION_2=$(grep -Po "LOCATION_2=\K.*" "$CONFIG_FILE" || true)
LOCATION_2=$(eval echo "$LOCATION_2")


# check
if [[ $START_DATE -lt $END_DATE ]]; then
    echo "Error: startdate $START_DATE is taller than enddate $END_DATE"
    exit 1
fi

# check
if [[ $DIRECTORY_IN == $DIRECTORY_OUT ]]; then
    echo "Error: DIRECTORY_IN and DIRECTORY_OUT are equal!!??"
    exit 1
fi

echo $directory


my_loop () {
    # get args
    my_date=$1
    DIRECTORY_IN=$2

    full_directory_in=$(eval echo "$DIRECTORY_IN")
    full_directory_out=$(eval echo "$DIRECTORY_OUT")
      
    # check if directory exists
    if [[ ! -d ${full_directory_in} ]]; then
        echo "Warning: DIRECTORY_IN not exists: ${full_directory_in}"
    else
        number_of_files=$(find ${full_directory_in} -maxdepth 1 -name ${FILENAME_IN_PATTERN} -printf 1 | wc -c)
  
        if [[ $number_of_files -lt 2 ]]; then
            echo "Warning: no files found at: ${full_directory_in}"
            exit
        else
            # create subdir
            if [[ ! -d ${full_directory_out} ]]; then
                echo "INFO: directory_out not exists: ${full_directory_out}"
                mkdir -p ${full_directory_out}
                echo "INFO: directory_out created: ${full_directory_out}"
            fi
            echo "INFO: in total number of pics found: $number_of_files"
      
        video_filename="${full_directory_out}${my_date}${FILENAME_OUT_PATTERN}"
        
        echo "INFO: Create video : $video_filename"

        cat $(find ${full_directory_in} -maxdepth 1 -name "${FILENAME_IN_PATTERN}" | sort -V) | \
             
        ffmpeg -framerate 20 -i - -vcodec libx264 -filter_complex "\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$INSTITUTION_PROJECT_1':fontsize=36:fontcolor=white:x=10:y=51,\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$INSTITUTION_PROJECT_2':fontsize=36:fontcolor=white:x=10:y=100,\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf':text='$LOCATION_1':fontsize=35:fontcolor=white:x=1620:y=51,\
        drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$LOCATION_2':fontsize=36:fontcolor=white:x=1620:y=100,\
        fade=type=in:duration=2:start_time=0,\
        scale=720:-1" $video_filename
        
        fi
    fi
  
}

while ! [[ $START_DATE > $END_DATE ]]; do
    echo $START_DATE
    
    my_loop $START_DATE "$DIRECTORY_IN" 
    
    START_DATE=$(date -d "$START_DATE + 1 day" +%F)
done
