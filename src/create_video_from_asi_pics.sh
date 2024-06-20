#!/bin/bash -e

# create a timelapse video from yesterday
#./create_video_from_asi_pics.sh -c pic2video.config

# create timelapse videos within a given period
#./create_video_from_asi_pics.sh -s 2023-12-12 -e 2023-12-22 -c pic2video.config 

#################################################################################
#Script Name	: create_video_from_asi_pics.sh                                                                                    
#Description	: The script creates a timelapse (video) from pics in a directory                                                                          
#Args           : configfile, optional(startdate, enddate)                                                                                   
#Author       	: Rico Hengst                                                                                       
#################################################################################



# set/get default 
CONFIG_FILE="../conf/pic2video.config"


display_usage() { 
    echo "##############################################################################"
    echo "### The script creates a timelapse (video) from pics in a directory" 
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
                echo "  -s <START_DATE>  optional   string = 2023-01-22"
                echo "  -e <END_DATE>    optional   string = 2024-11-30"
                echo "  -c <CONFIG_FILE> mandatory  string = "
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


# check config file
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Error: configfile not exists: $CONFIG_FILE"
  exit 1
fi

# check if DATES are provided, otherwise get from config
if [[ -z "$START_DATE" || -z "$END_DATE" ]]
then
    echo "START_DATE or STOP_DATE are not provided"
    echo "Get START_DATE, END_DATE from config"
    START_DATE=$(grep -Po "START_DATE=\K.*" "$CONFIG_FILE" || true); # echo 4: $START_DATE
    START_DATE=$(eval echo "$START_DATE"); # echo 4: $START_DATE

    END_DATE=$START_DATE
fi


# get config content
DIRECTORY_IN=$(grep -Po "DIRECTORY_IN=\K.*" "$CONFIG_FILE" || true)
DIRECTORY_IN=$(eval echo "$DIRECTORY_IN")

DIRECTORY_OUT=$(grep -Po "DIRECTORY_OUT=\K.*" "$CONFIG_FILE" || true)
DIRECTORY_OUT=$(eval echo "$DIRECTORY_OUT")

FILENAME_IN_PATTERN=$(grep -Po "FILENAME_IN_PATTERN=\K.*" "$CONFIG_FILE" || true)
FILENAME_IN_PATTERN=$(eval echo "$FILENAME_IN_PATTERN")

FILENAME_OUT_PATTERN=$(grep -Po "FILENAME_OUT_PATTERN=\K.*" "$CONFIG_FILE" || true)
FILENAME_OUT_PATTERN=$(eval echo "$FILENAME_OUT_PATTERN")

TEXT_TOP_LEFT_1=$(grep -Po "TEXT_TOP_LEFT_1=\K.*" "$CONFIG_FILE" || true)
TEXT_TOP_LEFT_1=$(eval echo "$TEXT_TOP_LEFT_1")

TEXT_TOP_LEFT_2=$(grep -Po "TEXT_TOP_LEFT_2=\K.*" "$CONFIG_FILE" || true)
TEXT_TOP_LEFT_2=$(eval echo "$TEXT_TOP_LEFT_2")

TEXT_TOP_RIGHT_1=$(grep -Po "TEXT_TOP_RIGHT_1=\K.*" "$CONFIG_FILE" || true)
TEXT_TOP_RIGHT_1=$(eval echo "$TEXT_TOP_RIGHT_1")

TEXT_TOP_RIGHT_2=$(grep -Po "TEXT_TOP_RIGHT_2=\K.*" "$CONFIG_FILE" || true)
TEXT_TOP_RIGHT_2=$(eval echo "$TEXT_TOP_RIGHT_2")


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
            
            if [[ -f ${video_filename} ]]; then
                echo "Warning: video file already exist: ${video_filename}"
                echo "Warning: video will be deleted ..."
                rm ${video_filename}
            fi
            
            echo "INFO: Create video : $video_filename"
            
            # find files in directory and sort
            cat $(find ${full_directory_in} -maxdepth 1 -name "${FILENAME_IN_PATTERN}" | sort -V) | \
            
            # generate video
            ffmpeg -framerate 20 -i - -vcodec libx264 -filter_complex "\
            drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$TEXT_TOP_LEFT_1':fontsize=36:fontcolor=white:x=10:y=51,\
            drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$TEXT_TOP_LEFT_2':fontsize=36:fontcolor=white:x=10:y=100,\
            drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed-Bold.ttf':text='$TEXT_TOP_RIGHT_1':fontsize=35:fontcolor=white:x=1620:y=51,\
            drawtext=fontfile='/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf':text='$TEXT_TOP_RIGHT_2':fontsize=36:fontcolor=white:x=1620:y=100,\
            fade=type=in:duration=0.5:start_time=0,\
            scale=720:-1" $video_filename
        
        fi
    fi
  
}

while ! [[ $START_DATE > $END_DATE ]]; do
    echo $START_DATE
    
    my_loop $START_DATE "$DIRECTORY_IN" 
    
    START_DATE=$(date -d "$START_DATE + 1 day" +%F)
done
