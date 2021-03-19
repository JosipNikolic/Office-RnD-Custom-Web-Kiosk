#!/usr/bin/env python3

#Basic required imports
import requests
import json
import os
import datetime
import sys
import time
from math import floor

#import used to get data from markup(HTML)
from bs4 import BeautifulSoup

#import used for human(natural) sorting
import re

#Config for logging
import logging


#Variables used for API request
today = datetime.date.today()
calendar_period_start=str(today)+"T08:00:00.000Z"
calendar_period_end=str(today)+"T19:00:00.000Z"

#Get destination folder location from command-line arguments passed to the script
folder_location=sys.argv[1]
html_to_edit=folder_location+"CodeHubCalendar.html"
log_file=folder_location+"CodeHubCalendar.log"
css_file=folder_location+"css/style2.css"
api_response_file=folder_location+"api_response"

logging.basicConfig(filename=log_file, filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%A %d/%m/%Y %H:%M:%S', level=logging.DEBUG)
log = logging.getLogger()


#Required API request info
api_url_base = 'https://code-hub-mostar.officernd.com/'
headers = {'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1'}

#Get current date and time
now = datetime.datetime.now()
now = now.strftime("%A %d/%m/%Y %H:%M")


### FUNCTIONS ###

#Functions for human sorting
def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s
    
def natural_sort(s):
    #Turn a string into a list of string and number chunks. "z23a" -> ["z", 23, "a"]
    return [ tryint(c) for c in re.split('([0-9]+)', str(s)) ]

def sort_nicely(l):
    #Sort the given list in the way that humans expect.
    l.sort(key=natural_sort)

#Function for retrieveing authurization cookie
def api_get_cookie():

    api_url = ('{0}oauth/token'.format(api_url_base))  
    
    try:
        response = requests.get(api_url, headers=headers)
    
        if response.status_code == 200:
            return response.headers['Set-Cookie']
        else:
            log.warning(" '[Get cookie] - Status code is not 200:: ' "+str(response.status_code))
            write_to_file(log_file, "\n", "a")
            return None
    except:
        log.exception(" 'Get cookie function failed' ")
        write_to_file(log_file, "\n", "a")
        return 0

#Function to get all reservations for selected period. Including ones that are canceled
def api_get_calendar(set_cookie):

    
    headers['Cookie']=set_cookie
    api_url = ('{0}i/organizations/code-hub-mostar/user/bookings/occurrences?$populate=resourceId._id,resourceId.name&start='+calendar_period_start+'&end='+calendar_period_end).format(api_url_base)   
    
    try:
        response = requests.get(api_url, headers=headers)
    
        if(response.status_code!=200):
            log.warning(" '[Get bookings] - Status code is not 200: ' "+str(response.status_code))
            write_to_file(log_file, "\n", "a")
            return None

        elif(response.text == "[]"):        
            log.info(" 'No reservations on this date' ")
            write_to_file(log_file, "\n", "a")
            return None
        else:
            return json.loads(response.content.decode('utf-8'))
    except:
        log.exception(" 'Get Bookings request failed' "+str(response.status_code))
        write_to_file(log_file, "\n", "a")
        return 0

#Function for filtering API data and finding resources that are reserved
def get_report_data_rnd(data, *resources):


    html_elements = []
    i=0

    reservation_start=reservation_end=None      #For storing reservation start and end time
    
    #Time zone adjustment
    time_zone_adjust=int(time.strftime("%z", time.localtime()))
    time_zone_adjust=int(time_zone_adjust/100)

    ##Collect live bookings only
    try:
        for element in data:
            #Filter reservations that are canceled or have identical start and end time
            if ( "canceled" in element or element['start']==element['end']):
                #Sometimes API returns "canceled: false" sometimes not, for events that are not canceled
                if(element["canceled"] is True):
                    print("", end="")

                else:
                    reservation_start=datetime.datetime.strptime(element['seriesStart'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                    reservation_start=reservation_start.strftime("%H:%M")
                    reservation_end=datetime.datetime.strptime(element['seriesEnd'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                    reservation_end=reservation_end.strftime("%H:%M")

                    html_elements.insert(i, [element['resourceId']['name'],reservation_start,reservation_end])
                    i+=1

            else:
                reservation_start=datetime.datetime.strptime(element['seriesStart'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                reservation_start=reservation_start.strftime("%H:%M")
                reservation_end=datetime.datetime.strptime(element['seriesEnd'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                reservation_end=reservation_end.strftime("%H:%M")

                html_elements.insert(i, [element['resourceId']['name'],reservation_start,reservation_end])
                i+=1
    except:
        log.exception(" 'Collecting live bookings failed' ")
        write_to_file(log_file, "\n", "a")
        return 0

    ##Create corresponding CSS
    if(len(html_elements)==0):     #For case when all events are canceled / deleted
        return 0

    else:
        #Sort HTML elements list by first column(resource name - index=0) and store them
        sort_nicely(html_elements)
        
        css_style=""

        try:
            for element in (html_elements):
                for j in range(len(resources)):
                    if element[0]==resources[j][0]:
                        hours, minutes = map(int, element[1].split(':'))
                        hours2, minutes2 = map(int, element[2].split(':'))

                        #Round start/end of the booking(minutes) to 0, 15, 30, 45
                        minutes=(floor(minutes/7.5)-floor(minutes/15))*15
                        minutes2=(floor(minutes2/7.5)-floor(minutes2/15))*15

                        #Calculate booking duration
                        diff= (hours2+(float(minutes2)/60)) - (hours+(float(minutes)/60))
                        booking_len=round(diff*102.35-5)

                        #Set CSS for div corresponding to booking
                        css_style+="#div"+str(j).zfill(2)+str(hours-7).zfill(2)+"{background-color: var(--busy); width:"+str(booking_len)+"%; margin-left: "+left_margin(minutes)+"%;}"
                    
                #Add new line to CSS (each #div in new line)
                css_style+="\n" 
            
            #Write generated CSS
            write_to_file(css_file, css_style,"w")

        except:
            log.exception(" 'Error ocurred while generating css' ")
            write_to_file(log_file, "\n", "a")
            return 0

        last_update()       
        return 1

#Generic function for writing data to file
def write_to_file(file_name, data_to_write, argument):

    try:
        f = open(file_name, argument)
        
        if(f):
            f.write(data_to_write)
            f.close()
            return 1

        else:
            return 0

    except:
        return 0

#Function for geting list of resources
def api_get_resource_list(set_cookie):

    headers['Cookie']=set_cookie
    api_url = ('https://app.officernd.com/i/organizations/code-hub-mostar/resources')

    try: 
        response = requests.get(api_url, headers=headers)
    
        if(response.status_code!=200):
            log.warning(" '[Get resource list] - Status code is not 200: ' "+str(response.status_code))
            write_to_file(log_file, "\n", "a")
            return None
        elif(response.text == "[]"):
            log.info(" '[Get resource list] - API response is empty' ")
            write_to_file(log_file, "\n", "a")
            return None
        else:
            resource_list = json.loads(response.content.decode('utf-8'))
            resource_names = []
            i=0
            for element in resource_list:
                resource_names.insert(i, [element['name']])
                i+=1
            sort_nicely(resource_names)
        return resource_names
    except:
        log.exception(" 'Get resource list request failed' ")
        write_to_file(log_file, "\n", "a")
        return 0

#Function for updating "Last update" section on page
def last_update():

    try:
        #Find table cell with last update info and replace value
        with open(html_to_edit, 'r') as file:
            fcontent = file.read()
            sp = BeautifulSoup(fcontent, 'lxml')
            sp.find(id='replace').string='Last update: '+str(now)
    
        #Enroll changes
        with open(html_to_edit, 'w') as fp:
            fp.write(str(sp))

        return 1

    except:
        log.exception(" 'Last update time on calendar is not updated' ")
        write_to_file(log_file, "\n", "a")
        return 0

#Function used to determine margin-left for booking
def left_margin(i):
        switcher={
                0: '1',
                15:'27',
                30:'54',
                45:'80.5',
             }
        return switcher.get(i, '0')

### FUNCTIONS ends here ###


###   MAIN   ###

try:
    #Retrieve authenticating cookie
    cookie = api_get_cookie()
    
    #If cookie is None, authorization will fail
    if(cookie is not None):
    
        resource_names=api_get_resource_list(cookie)
        api_booking_data = api_get_calendar(cookie)     
        
        #Try to open file that contains last API response. If there is no such file (first time runing), use empty string
        try:
            f = open(api_response_file, "r")
            temp_char=f.read()
            f.close()
        except:
            temp_char=""        
            log.exception(" 'Cannot open file that contains last API response' ")
            write_to_file(log_file, "\n", "a")
            pass
    
        #Compare new API response with last one
        if( temp_char==str(api_booking_data) ):
            log.info(" 'Identical API response content' ")
            write_to_file(log_file, "\n", "a")         
            last_update()
    
        #If new API response is not identical, check does it contain any data
        elif ( api_booking_data is not None):
            get_report_data_rnd(api_booking_data, *resource_names)
            write_to_file(api_response_file, str(api_booking_data), "w")
    
            last_update()
    
        #If new API response is different then previous one and it does not contain any data, make blank HTML page
        else:
            write_to_file(css_file, "","w")    
            last_update()
            
        logging.shutdown()   
    else:
        log.info("Cookie could not be retrieved")
        write_to_file(log_file, "\n", "a")
        logging.shutdown()

except:
    log.exception(" 'MAIN part of script failed' ")
    write_to_file(log_file, "\n", "a")
    logging.shutdown()