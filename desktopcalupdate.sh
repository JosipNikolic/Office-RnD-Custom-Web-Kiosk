#!/bin/bash
#This script is used to update the local web calendar information with data retrieved from the online OfficeRnD calendar and parse it then present
#it in a more concise, readable and less encumbering form for system resources

#Set up the needed env variables:
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000

#Setable variables that appear in multiple places inside the script:

#File and folder locations:
logfile=/home/pi/kiosklog/calendar.log #This is the script's log file
plcbkg=/home/pi/Pictures/CH3D.jpg #Placeholder desktop background
calapi=/home/pi/scripts/kioskcal/calendar_api.py #The location of the python script that generate the kiosk web calendars HTML & CSS
caldir=/home/pi/scripts/kioskcal/ #The folder in which the HTML, CSS & other files will be generated/updated by the calendar_api.py script
midscript=/home/pi/scripts/midorikiosk.sh #Location of the Midori web kiosk update/launch script
webcalscr=/home/pi/Pictures/OfficeRnDcal.png #The web calendar callback screenshot
webcalwal=/home/pi/Pictures/OfficeRnDcalwall.png #The current web calendar wallpaper location


#CutyCapt operational parameters:
ctct_mw=1920 #CutyCapt screenshot width
ctct_mh=1080 #CutyCapt screenshot height
ctct_d=9000 #CutyCapt screenshot page load delay

#Convert:
cropxyz=1630x700+270+135 #Convert's crop mode position and dimensions

#Web resources:
webcalurl='https://code-hub-mostar.officernd.com/public/calendar?rate.$ne=null' #The URL of your OfficeRnD web calendar

#Until loop variables:
webcalretry=5 #The number of tries to reach the OfficeRnD web calendar
n=0 #The loop counter should count down to 0 (zero)


#Log the start of the script:
echo -ne "\nStart calendar information update for desktop background calendar:\t" >> "$logfile"
date >> "$logfile"

#Display a message that the script has started on the main display and to the user(s):
echo -e "Updating calendars..." | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=15000 --fade-out=1 --position=4 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
echo -e "Updating calendars..." | wall


#Check if the OfficeRnd web calendar is accessible on the Internet and only proceed if it is:
until [ "$n" -ge "$webcalretry" ] #Try to reach the web calendar URL
do
	if wget --no-check-certificate --spider --server-response "$webcalurl" > /dev/null  2>&1 ; then
	break
	else
	n=$((n+1))
	fi
done

#If the OfficeRnD calendar is unavailable log its unavailability, reset to the default wallpapaer and exit:
if [ "$n" -ge "$webcalretry" ] ; then
echo -e "Unable to download new calendar info!" | tee -a "$logfile" | wall #Log the fact that the OfficeRnd web calendar was not accessible
DISPLAY=:0 pcmanfm --wallpaper-mode=stretch --set-wallpaper "$plcbkg" #Use pcmanfm to reset the desktop background on display:0
echo -e "Unable to download new calendar info!" |  aosd_cat --font "Liberation Sans 40" --fore-color red --shadow-color lightred --back-color black --transparency=2 --fade-in=1 --fade-full=20000 --fade-out=1 --position=7 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset -100 --shadow-offset 3 --padding 0 & #Display the fact that the OfficeRnd web calendar was not accessible
exit 1 #Stop script with an error code of '1' to stderr

else #Proceed with web calendar download and update
#Announce and log that the new OfficeRnD calendar data is being downloaded
echo -e "Downloading new calendar info!" | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=20000 --fade-out=1 --position=7 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset -100 --shadow-offset 3 --padding 0 &
echo -e "Downloading new calendar info!" | tee -a "$logfile" | wall

	#Check if the Python script parses the calendar correctly, log and display success or failure and provide a directory where to dump the resulting files:
	if python3 "$calapi" "$caldir" ; then #If the calendar_api.py script successfully runs with Python3 announce and log that
	echo -e "Python: web calendar successfully parsed." | tee -a "$logfile" | wall
	echo -e "Python: web calendar successfully parsed." | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=20000 --fade-out=1 --position=7 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
	true #Placeholder

	else  #If the calendar_api.py script fails to run with Python3 announce and log that
	echo -e "Python: web calendar parse error!" | tee -a "$logfile" | wall
	echo -e "Python: web calendar parse error!" | aosd_cat --font "Liberation Sans 40" --fore-color red --shadow-color lightred --back-color black --transparency=2 --fade-in=1 --fade-full=20000 --fade-out=1 --position=7 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
	false #Placeholder
	fi

	#Check if the Midori browser is running (probably with the web calendar open) and if it is running launch the Midori launch/update module:
	if pgrep -x "midori" > /dev/null 2>&1 ; then #If Midori is open run the Midori web kiosk update/launch script (to update the displayed information)
	echo -e "Updating web calendar!" >> "$logfile" #Log Midori update/launch script launch
	sleep 30 #Lower load/time to breathe
	setsid -f bash "$midscript" & #Launch the web calendar launch/update module as a separate process to update the displayed web calendar
	true #Placeholder
	else

	#If Midori is not running there must be a good reason so log it and fallback to displaying the meeting room calendar as a desktop background:
	echo -e "Updating desktop background calendar!" >> "$logfile" #Log the web calendar desktop background update
	DISPLAY=:0 cutycapt --min-width="$ctct_mw" --min-height="$ctct_mh" --delay="$ctct_d" --url="$webcalurl" --out="$webcalscr" #Create a screenshot of the web calendar
	sleep 5 #Lower load/time to breathe
	nice convert "$webcalscr" -crop "$cropxyz" "$webcalwal" #Crop the web calendar screenshot for display (while not hogging system resources)
	sleep 5 #Lower load/"time to breathe"
	false #Placeholder
	fi
	#Once the screenshot created by CutyCapt is ready, cropped by convert and stored in a file set it as the wallpaper or update the existing wallpaper web calendar with it:
	if DISPLAY=:0 pcmanfm --wallpaper-mode=stretch --set-wallpaper "$webcalwal" ; then #Set the cropped web calendar screenshot as the new wallpaper

	#Announce and log (with more detail) the web calendar's successfull update:
	echo -e "Calendar updated at $(date +%H:%M:%S)" | tee -a "$logfile" | wall
	echo -e "Calendar updated at $(date +%H:%M)" | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=20000 --fade-out=1 --position=4 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
	true #Placeholder
	fi
fi
