#!/bin/bash
#This script is used to launch Midori with the localy generated web calendar open on the main display screen.
#Then the script will grab and focus the brower window on screen and resize it to fullscreen and exit.
#If Midori is already running this script will grab and focus the browser window on screen and refresh the web calendar then exit.
#This script was created in order to be called by other scripts

#Set up the needed env variables:
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000

#Setable variables that appear in multiple places inside the script:
logfile=/home/pi/kiosklog/midori.log #This is the script's log file
HTMLcal=/home/pi/scripts/kioskcal/CodeHubCalendar.html #The HTML file of the webcalendar to be displayed in Midori (produce by desktopcalupdate.sh with calendar_api.py)

date >> $logfile #Log the start of this script
midpid=$(pidof midori) #Store the PID of the Midori web browser process if it exists in this variable

if pgrep -x "midori" > /dev/null 2>&1 ; then #If Midori is already running do:
#Announce and log that Midori is already running and that the web calendar data being displayed is about to be refreshed:
echo -e "Midori is running -|- Refreshing web calendar data..." | aosd_cat --font "Liberation Sans 39" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
echo -e "Midori is running -|- Refreshing web calendar data..." | tee -a "$logfile" | wall
#Announce and log that the Midori window is about to be grabbed and focused on the display:
echo -e "Grabbing web kiosk window..." | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 100 --shadow-offset 3 --padding 0 &
echo -e "Grabbing web kiosk window..." | tee -a "$logfile" | wall

	if wmctrl -R "CodeHub Mostar Calendar" ; then #Use wmctrl to grab the open Midori window by the open HTML document title
	sleep 1 #Wait for the grabbed Midori window to focus
	#Announce and log that the calendar data is about to be refreshed:
	echo -e "Refreshing web calendar data..." | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 200 --shadow-offset 3 --padding 0 &
	echo -e "Refreshing web calendar data..." | tee -a "$logfile" | wall
	DISPLAY=:0 xte 'key F5' #Send the 'F5' key to the now focused Midori window on DISPLAY:0 with the xautomation tool to trigger a browser page refresh
	true #Placeholder
	else
	#If something goes wrong while trying to grab the Midori window announce and log that and then exit:
	echo -e "Unable to grab web calendar window!" | aosd_cat --font "Liberation Sans 40" --fore-color red --shadow-color lightred --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 200 --shadow-offset 3 --padding 0 &
	echo -e "Unable to grab web calendar window!" | tee -a "$logfile" | wall
	false #Placeholder
	fi
true #Placeholder

else #If Midori is not running launch Midori:
#Announce and log that the Midori web browser was not running and is about to be launched:
echo -e "Web calendar is not running -|- Launching web calendar!" | aosd_cat --font "Liberation Sans 37" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
echo -e "Web calendar is not running -|- Launching web calendar!" | tee -a "$logfile" | wall
setsid -f midori -p --execute=fullscreen "$HTMLcal" & #Launch Midori in incognito mode and open the local web calendar HTML page by forking off the current environment into it's own session
sleep 30 #Wait for Midori to start and fully load the HTML page
#Announce and log that the Midori window is about to be grabbed and focused on the display:
echo -e "Grabbing web kiosk window..." | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 0 --shadow-offset 3 --padding 0 &
echo -e "Grabbing web kiosk window..." | tee -a "$logfile" | wall

	if wmctrl -R "CodeHub Mostar Calendar" ; then #Use wmctrl to grab the open Midori window by the open HTML document title
	sleep 3 #Wait for the grabbed Midori window to focus
	DISPLAY=:0 xte 'key F11' #Send the 'F11' key to the now focused Midori window on DISPLAY:0 with the xautomation tool to trigger pseudo fullscreen mode
	#Announce and log that the Midori window is being resized:
	echo -e "Resizing web kiosk window..." | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 100 --shadow-offset 3 --padding 0 &
	echo -e "Resizing web kiosk window..." | tee -a "$logfile" | wall
	sleep 3 #Wait for the Midori window to resize
	DISPLAY=:0 xte 'key F11' #Send the 'F11' key to the Midori window on DISPLAY:0 again with the xautomation tool to trigger fullscreen mode
	#Announce and log that the Midori window was successfully resized:
	echo -e "Web kiosk window resized!" | aosd_cat --font "Liberation Sans 40" --fore-color green --shadow-color lightgreen --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 200 --shadow-offset 3 --padding 0 &
	echo -e "Web kiosk window resized!" | tee -a "$logfile" | wall
	else
	#If something goes wrong while trying to grab the Midori window announce and log that and then exit:
	echo -e "Unable to grab web calendar window!" | aosd_cat --font "Liberation Sans 40" --fore-color red --shadow-color lightred --back-color black --transparency=2 --fade-in=1 --fade-full=4998 --fade-out=1 --position=1 --lines=0 --fore-opacity 255 --shadow-opacity 192 --back-opacity 1 --x-offset -20 --y-offset 100 --shadow-offset 3 --padding 0 &
	echo -e "Unable to grab web calendar window!" | tee -a "$logfile" | wall
	false #Placeholder
	fi
false #Placeholder
fi
echo >> "$logfile" #Put a newline in the logfile for formatting purposes
unset midpid #Unset the variable containing the Midori PID ; just in case...
