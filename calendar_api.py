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
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter

#Variables used for API request
rnd_office="5b7e9a8a87daf911009d43aa"
today = datetime.date.today()
calendar_period_start=str(today)+"T08:00:00.000Z"
calendar_period_end=str(today)+"T19:00:00.000Z"

#Get destination folder location from command-line arguments passed to the script
folder_location=sys.argv[1]
html_to_edit=folder_location+"CodeHubCalendar.html"
log_file=folder_location+"logs/CodeHubCalendar.log"
css_file=folder_location+"css/style2.css"
api_response_file=folder_location+"api_response"

#logging.basicConfig(filename=log_file, filemode='a', format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%A %d/%m/%Y %H:%M:%S', level=logging.DEBUG)
log = logging.getLogger()
handler = TimedRotatingFileHandler(filename=log_file, when='D', interval=1, backupCount=30, encoding='utf-8', delay=False)
formatter = Formatter(fmt='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%A %d/%m/%Y %H:%M:%S')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)



#Required API request info
api_url_base = 'https://code-hub-mostar.officernd.com/'
headers = {'Accept': 'application/json',
            'DNT': '1'}            
#'Accept-Encoding': 'gzip, deflate, br',

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
            if ( "canceled" in element or element['start']==element['end']):  #Filter reservations that are canceled or have identical start and end time
                if(element["canceled"] is True):    #Sometimes API returns "canceled: false" sometimes not, for events that are not canceled
                    print("",end="")

                else:
                    reservation_start=datetime.datetime.strptime(element['start']['dateTime'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                    reservation_start=reservation_start.strftime("%H:%M")
                    reservation_end=datetime.datetime.strptime(element['end']['dateTime'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                    reservation_end=reservation_end.strftime("%H:%M")

                    html_elements.insert(i, [element['resourceId']['name'],reservation_start,reservation_end])
                    i+=1

            else:
                reservation_start=datetime.datetime.strptime(element['start']['dateTime'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
                reservation_start=reservation_start.strftime("%H:%M")
                reservation_end=datetime.datetime.strptime(element['end']['dateTime'],'%Y-%m-%dT%H:%M:%S.%fZ')+datetime.timedelta(hours=time_zone_adjust)
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

                        if diff==0: #All day reservations have the same hh:mm:ss, but different date (24 hours total differnce)
                            #Set CSS for div corresponding to booking
                            css_style+="#div"+str(j).zfill(2)+"01"+"{background-color: var(--busy); width:1121%; margin-left: 1%;}"
                        else:
                            #booking_len=floor(102.4*diff-2.4)-1
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
            #resource_list = json.loads('[{"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"meeting_room","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","62069ad5cc28b20e000118d6","62069ae2b202dcfca76c0ac3"],"_id":"5b7fed8a989a6d0f00ad56f0","office":"5b7e9a8a87daf911009d43aa","name":"Meeting Room #1","number":1,"size":5,"rate":"6206a0c4cc28b27eff013238","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T11:35:38.905Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#f7d42a","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/meeting-room-1614441298818.jpeg","room":"611b88e813b4ab75c38e7bdb","target":"611b8f818a40c0071478b9e6","order":1,"timezone":"Europe/Sarajevo","status":"meeting_room"},{"access":{"full":true,"public":false,"teams":[],"plans":["6207bf759fc1062ef6b2bd52","621b52590ba8118e2df049e9","621b545cd25dce408623b2df","621b61a74bbdb7dbad5ab4c0","621b61dd9598512fe29011c8","6228b0dc62af7ef691a3e014","6228b85981bfa226f28ca5d4"]},"price":0,"deposit":0,"parents":[],"type":"meeting_room","_id":"5b7fed9e87daf911009e606f","office":"5b7e9a8a87daf911009d43aa","name":"Skype room #1","number":2,"size":1,"rate":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T11:35:58.439Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#f7d42a","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/skype-room-1-1614441343187.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611be170a02481db0e448e3a","order":4,"timezone":"Europe/Sarajevo","status":"meeting_room"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ff97887daf911009e6aa0","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #1","number":3,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:26:32.156Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-1-1614441393183.jpeg","color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a92cca8ba14ed4403f08c","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ff9d3a32a360f002da2a5","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #3","number":4,"parent":null,"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-3-1614441479720.jpeg","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:28:03.956Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"targetPlan":null,"color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9313f0b5eed5a47cf207","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffa4c87daf911009e6bad","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #5","number":5,"parent":null,"targetPlan":null,"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-5-1614441751035.jpeg","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:30:04.937Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9314f0b5ee8bcc7cf20c","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffa68a32a360f002da327","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #7","number":6,"parent":null,"targetPlan":null,"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-7-1614441530413.jpeg","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:30:32.572Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9314a8ba1429c503f537","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffa7f87daf911009e6bda","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #8","number":7,"parent":null,"targetPlan":null,"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-8-1614441544325.jpeg","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:30:55.989Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9329f0b5ee62ed7cf28f","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffb0687daf911009e6c29","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #6","number":8,"parent":null,"targetPlan":null,"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-6-1614441518387.jpeg","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:33:10.475Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9329f0b5ee10d87cf293","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffb1aa32a360f002da398","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #4","number":9,"parent":null,"targetPlan":null,"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-4-1614441497088.jpeg","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:33:30.636Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9329f0b5ee11697cf28d","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffb27a32a360f002da3ab","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #2","number":10,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:33:43.719Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-2-1614441458249.jpeg","color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9314a8ba14ccb703f539","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffce587daf911009e6daa","office":"5b7e9a8a87daf911009d43aa","name":"Desk #2","number":11,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:41:09.295Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#e557a0","rate":"622a13ffd81b0b2d9dd6e7d7","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-2-1536055449412.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b82ed42320ed14f8121d5","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b7ffcfb989a6d0f00ad63f0","office":"5b7e9a8a87daf911009d43aa","name":"Desk #1","number":12,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T12:41:31.706Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"color":"#e557a0","rate":"622a13ffd81b0b2d9dd6e7d7","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-1-1536055318268.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b82ed13b4ab973e8d8bb1","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b80015cc39bf80f00d2b212","office":"5b7e9a8a87daf911009d43aa","name":"Desk #3","number":13,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#e557a0","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T13:00:12.531Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-3-1536055540281.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b82ee42320e71e38123ca","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b800172989a6d0f00ad66ea","office":"5b7e9a8a87daf911009d43aa","name":"Desk #4","number":14,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#e557a0","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T13:00:34.648Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-4-1536055727056.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b82d213b4ab06048d88ea","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b80018687daf911009e70c3","office":"5b7e9a8a87daf911009d43aa","name":"Desk #5","number":15,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#e557a0","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T13:00:54.230Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-5-1536055860832.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b82d242320e4ea68120f9","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b80019aa32a360f002da86f","office":"5b7e9a8a87daf911009d43aa","name":"Desk #6","number":16,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#e557a0","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T13:01:14.425Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-6-1536055920520.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b82d213b4ab33958d88f0","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5b8001ca87daf911009e7119","office":"5b7e9a8a87daf911009d43aa","name":"Desk #7","number":17,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#e557a0","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2018-08-24T13:02:02.793Z","createdBy":"5b59bff940046510000f6faa","availability":[{"startDate":"2018-08-24T00:00:00.000Z","endDate":null}],"image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-7-1536055962277.jpeg","room":"611a8b4eac02cad7c55ff43f","target":"611b81d0e7ec442f1f025fb9","timezone":"Europe/Sarajevo","status":"hotdesk"},{"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"meeting_room","amenities":["62069a13a0b1e66616612abf","62069ad5cc28b20e000118d6","62069ae2b202dcfca76c0ac3","62069a9eb202dc0ecb6c0923","62069a80cc28b28d9b01176a"],"_id":"5d0a2b4443d4f100db99104c","office":"5b7e9a8a87daf911009d43aa","name":"Mini meeting room","availability":[{"startDate":"2019-06-19T00:00:00.000Z","endDate":null}],"number":20,"size":2,"rate":"62067f769fc106f038afc6eb","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-06-19T12:32:04.182Z","createdBy":"5b59bff940046510000f6faa","color":"#f7d42a","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/mini-meeting-room-1614441328428.jpeg","room":"611b88e813b4ab75c38e7bdb","target":"611b8fbf8a40c0f45178bcc6","order":3,"timezone":"Europe/Sarajevo","status":"meeting_room"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5dfbd364687576001031d1fa","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #9","availability":[{"startDate":"2019-12-19T00:00:00.000Z","endDate":null}],"number":21,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-12-19T19:45:40.835Z","createdBy":"5b59bff940046510000f6faa","rate":"622a13ffd81b0b2d9dd6e7d7","color":"#00aeef","room":"611a8b4eac02cad7c55ff43f","target":"611a942da9f500f06f6ec304","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-9-1614441766723.jpeg","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5dfbd37cb383f8003ce8249a","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #10","availability":[{"startDate":"2019-12-19T00:00:00.000Z","endDate":null}],"number":22,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-12-19T19:46:04.215Z","createdBy":"5b59bff940046510000f6faa","color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a947b5a40b7703fe0c793","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-10-1614441571247.jpeg","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5dfbd38eb383f8003ce827f9","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #11","availability":[{"startDate":"2019-12-19T00:00:00.000Z","endDate":null}],"number":23,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-12-19T19:46:22.352Z","createdBy":"5b59bff940046510000f6faa","color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9473a9f5006ac36ec4eb","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-11-1614441583696.jpeg","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5dfbd39bb383f8003ce82964","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #12","availability":[{"startDate":"2019-12-19T00:00:00.000Z","endDate":null}],"number":24,"parent":null,"targetPlan":null,"organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-12-19T19:46:35.553Z","createdBy":"5b59bff940046510000f6faa","color":"#00aeef","rate":"622a13ffd81b0b2d9dd6e7d7","room":"611a8b4eac02cad7c55ff43f","target":"611a9482a9f50087766ec525","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-12-1614441595745.jpeg","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5dfbd42eb383f8003ce83f94","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #13","availability":[{"startDate":"2019-12-19T00:00:00.000Z","endDate":null}],"number":25,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#00aeef","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-12-19T19:49:02.359Z","createdBy":"5b59bff940046510000f6faa","room":"611a8b4eac02cad7c55ff43f","target":"611a94735a40b77044e0c737","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-13-1614441607997.jpeg","timezone":"Europe/Sarajevo","status":"hotdesk"},{"move":null,"access":{"full":true,"public":false,"teams":[],"plans":[]},"price":0,"deposit":0,"parents":[],"type":"hotdesk","amenities":["62069a13a0b1e66616612abf","62069a80cc28b28d9b01176a","62069a9eb202dc0ecb6c0923","6207bd2419698f8551a75b2e","6207bd2f156d4a5fac0381f3","6207bd4b156d4a66240381f8"],"_id":"5dfbd44eb383f8003ce842c3","office":"5b7e9a8a87daf911009d43aa","name":"Desk + Monitor #14","availability":[{"startDate":"2019-12-19T00:00:00.000Z","endDate":null}],"number":26,"parent":null,"targetPlan":null,"rate":"622a13ffd81b0b2d9dd6e7d7","color":"#00aeef","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2019-12-19T19:49:34.504Z","createdBy":"5b59bff940046510000f6faa","room":"611a8b4eac02cad7c55ff43f","target":"611a94825a40b768dce0c7ae","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/desk-monitor-14-1614441625309.jpeg","timezone":"Europe/Sarajevo","status":"hotdesk"},{"access":{"full":true,"public":false,"teams":[],"plans":["621b545cd25dce408623b2df"]},"price":0,"deposit":0,"parents":[],"type":"meeting_room","amenities":["62069a13a0b1e66616612abf","62069ad5cc28b20e000118d6","62069ae2b202dcfca76c0ac3","62069a9eb202dc0ecb6c0923","62069a80cc28b28d9b01176a"],"_id":"620293a68abe6b6f433074aa","office":"5b7e9a8a87daf911009d43aa","room":"6206943ab202dca4f86bde35","name":"Meeting Room #2","availability":[{"startDate":"2022-02-25T00:00:00.000Z"}],"number":27,"size":6,"area":15000000,"rate":"62069b42a0b1e6ea86613348","organization":"5b7e9a8a87daf911009d43a9","createdAt":"2022-02-08T16:00:38.518Z","createdBy":"5be3088f66a0f81000dccf8a","description":"Meeting room located downstairs","color":"#f7d42a","image":"//dzrjcxtasfoip.cloudfront.net/user-resources/organization/meeting-room-2-1663746184478.jpeg","order":2,"timezone":"Europe/Sarajevo","status":"meeting_room"}]')
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
            temp_char=json.loads(temp_char)
            f.close()
        except:
            temp_char=""        
            log.exception(" 'Cannot open file that contains last API response, using empty string as last API response for comparison' ")
            write_to_file(log_file, "\n", "a")
            pass
        
        #Compare new API response with last one
        if( temp_char==api_booking_data ):
            log.info(" 'Identical API response content' ")
            write_to_file(log_file, "\n", "a")         
            last_update()

        #If new API response is not identical, check does it contain any data
        elif ( api_booking_data is not None):
            get_report_data_rnd(api_booking_data, *resource_names)
            api_booking_data_pretty = json.dumps(api_booking_data, indent=4, sort_keys=True)
            write_to_file(api_response_file, str(api_booking_data_pretty), "w")
    
            last_update()
    
        #If new API response is different then previous one and it does not contain any data, rewrite CSS so HTML page will be blank
        else:
            write_to_file(css_file, "","w")    
            last_update()
        
        write_to_file(log_file, "\n", "a")    
        logging.shutdown()   
    else:
        log.info("Cookie could not be retrieved")
        write_to_file(log_file, "\n", "a")
        logging.shutdown()

except:
    log.exception(" 'MAIN part of script failed' ")
    write_to_file(log_file, "\n", "a")
    logging.shutdown()