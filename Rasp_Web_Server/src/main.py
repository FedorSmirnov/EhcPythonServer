'''
Created on Jan 17, 2014

@author: fedor
'''

# library imports
import web
import json
import telnetlib
import threading
import copy
import time
import urllib2

# local imports
from local import rasp_to_fhem_comm
from util import checkExtIp
from fhem import constants
from fhem import control


######## mapping of the URLs to the controller classes
urls = ('/', 'index', '/handshake', 'handshake')

######## credentials (perhaps good idea to add encryption later)
password_tr = 'geheim'
user_tr = 'guest@jochen-bauer.net'

######## variables used for the apartment behavior

# # lamp-movement behavior
lamp_movement_reaction = False  # movement sensitive or not

time_of_last_movement = None  # last moment when movement was registered
no_movement_interval = 60  # how long is the lamp on after the last registered movement

# # water sensor-flower behavior
time_of_last_wet_state = None
no_water_interval = 60

# # variables for the mold message
mold_temp = 10
mold_humidity = 70

######## variables for the used urgent alarms

alarms_urgend_all = False
alarmsUrgentList = []

alarm_ur_water = False
alarm_ur_water_message = 'Wasser laueft aus. Bitte dringend die Washmaschine ueberpruefen!!!'

######## variables for the used normal alarms
alarms_all = False
alarmList = []

alarm_water = False
alarm_water_message = 'Das Wasser ist ausgelaufen.'

alarm_flowers = False
alarm_flowers_message = 'Die Blumen wurden seit %d Minuten nicht gegossen.'

alarm_wind = False
alarm_wind_message = 'Sowohl die Eingangstuer als auch das Fenster sind geoeffnet.'

alarm_mold = False
alarm_mold_message = 'Die Luftfeuchtigkeit im Badezimmer ist zu hoch. Sie sollten lueften oder die Heizung einschalten, um Schimmelbefall zu vermeiden.'

# last time gong was checked
gong_check = None
gong_check_interval = 15



# function to check the water alarm
def check_water_alarm():
    global alarm_water
    if apartment.get_sens_status('Fedors_Zimmer', 'Wasserstand') == 'wet':
        alarm_water = True
    else:
        alarm_water = False

def check_flowers_alarm():
    global alarm_flowers
    if time_of_last_wet_state:
        if time.time() - time_of_last_wet_state > int(float(no_water_interval)):
            alarm_flowers = True
        else:
            alarm_flowers = False
    else:
        alarm_flowers = False

def update_alarm():
    global alarms_all
    global alarmList
    alarmList = []
    check_water_alarm()
    check_flowers_alarm()
    
    # if alarm_water:
    #    alarmList.append(alarm_water_message)
    
    if alarm_flowers:
        alarmList.append(alarm_flowers_message % ((time.time() - time_of_last_wet_state) / 60))
        
    if alarm_wind:
        alarmList.append(alarm_wind_message)
        
    if alarm_mold:
        alarmList.append(alarm_mold_message)
    
    # this line determines which alarms are active
    alarms_all = (alarm_flowers or alarm_wind or alarm_mold)
    
    
    
    global alarms_urgend_all
    global alarmsUrgentList
    alarmsUrgentList = []
    if alarm_ur_water:
        alarmsUrgentList.append(alarm_ur_water_message)
        
    alarms_urgend_all = alarm_ur_water

# function describing time dependent behavior
def check_times():
    
    # motion dependent lamp behavior 
    global lamp_movement_reaction    
    if lamp_movement_reaction and apartment.get_dev_status('Fedors_Zimmer', 'Lampe') == 'off':
    
        # turn the lamp of if no movement detected for the specified time 
        global time_of_last_movement
        global no_movement_interval
        if time_of_last_movement:
            time_delta = time.time() - time_of_last_movement
            if time_delta > no_movement_interval:
                control.set_dev_state('Fedors_Zimmer', 'Lampe', 'off')
                time_of_last_movement = None
    
    # alarm reaction
    update_alarm()
    
    global gong_check
    
    if not gong_check or time.time() - gong_check >= gong_check_interval:
        
        if (alarms_all or alarms_urgend_all) and apartment.get_dev_status('Fedors_Zimmer', 'Blinken') == 'off':
            apartment.set_dev_state('Fedors_Zimmer', 'Blinken', 'on')
            control.set_dev_state('Fedors_Zimmer', 'Blinken', 'on')
        
    
        
         
        if alarms_urgend_all and apartment.get_dev_status("Fedors_Zimmer", "Sound") == "off":
            apartment.set_dev_state('Fedors_Zimmer', 'Sound', 'on')
            control.set_dev_state('Fedors_Zimmer', 'Sound', 'on')
        
        gong_check = time.time()
    
    
        
    thread_timer = threading.Timer(0, check_times)
    thread_timer.setDaemon(True)
    thread_timer.start()   

# function used for the event listening
def listen_to_events():
        
    tn = telnetlib.Telnet(constants.HOST, constants.PORT_TELNET)
    tn.write('inform timer\n')
    index, match_object, text = tn.expect(constants.REG_LIST)
    tn.write('exit\n')
    time_mov = match_object.group(1)
    room = match_object.group(2) 
    dev_name = match_object.group(3)
    apartment.get_lock().acquire()
    if index == 0:
        if lamp_movement_reaction and apartment.get_dev_status('Fedors_Zimmer', 'Lampe') == 'off':
            # Event caused by a motion detector
            apartment.set_sens_state(room, 'motion', time_mov)
            
            # Motion => turn the lamp on
            control.set_dev_state('Fedors_Zimmer', 'Lampe', 'on')
            global time_of_last_movement
            time_of_last_movement = time.time()
    if index == 1:
        # Event caused by a temperature/humidity sensor  
        temp = match_object.group(4)
        humid = match_object.group(5)
        
        temp_int = float(temp)
        humid_int = float(humid)
        global alarm_mold
        
        if temp_int >= mold_temp and humid_int >= mold_humidity:
            alarm_mold = True
        else:
            alarm_mold = False
        
        apartment.set_sens_state(room, 'temperature', temp)
        apartment.set_sens_state(room, 'humidity', humid)
    if index == 2:
        if dev_name == 'Lampe' and lamp_movement_reaction:
            # if the lamp reacts to movement, the events do not affect the apartment state
            pass
        else:
            # Event caused by a switch
            state = match_object.group(4)
            apartment.set_dev_state(room, dev_name, state)
    if index == 3:
        # Event caused by a door sensor
        state = match_object.group(4)
        apartment.set_sens_state(room, dev_name, state)
        
        # TO DO: Add the second sensor to the alarm condition
        state_door = apartment.get_sens_status('Fedors_Zimmer', 'Tuer')
        state_window = apartment.get_sens_status('Fedors_Zimmer', 'Fenster')
        global alarm_wind
        if state_door == 'open' and state_window == 'open':
            alarm_wind = True
        else:
            alarm_wind = False
        
    if index == 4:
        # Event caused by a water sensor
        state = match_object.group(4)
        apartment.set_sens_state(room, dev_name, state)
        # Flower behavior
        global time_of_last_wet_state
        if state == 'dry' and dev_name == 'Wasserstand':
            # switch from wet to dry is seen as the last water moment
            time_of_last_wet_state = time.time()
        elif dev_name == 'Wasserstand':
            time_of_last_wet_state = None
        
        global alarm_ur_water
        
        if state == 'wet' and dev_name == 'Wasseralarm':
            alarm_ur_water = True
        elif dev_name == 'Wasseralarm':
            alarm_ur_water = False
        
        
    apartment.get_lock().release()
    tn.close()
    # When finished with the reading, the function calls itself in a new thread to keep listening
    thread_timer = threading.Timer(0, listen_to_events)
    thread_timer.setDaemon(True)
    thread_timer.start()    



#####################################################################################################
##############################  START OF THE PYSERVER  ##############################################
#####################################################################################################

# get your own external IP and report it to the web server (periodically repeated in an extra thread)
checkExtIp.checkIP()

# init of the object representing the state of all controlled devices
apartment = rasp_to_fhem_comm.init()


# start the thread listening for the fhem events
listen_to_events()

# start the thread managing the time dependent events
check_times()

class handshake:
    
    def GET(self):
        # gets called when the mobile client checks whether it can reach the PyServer via the local network
        return 'true'

class index:
    
    def GET(self):
        # Get the request data and look whether the correct credentials were provided
        data = web.input();
        if 'Password' not in data or 'User' not in data:
            raise web.NotFound()
        password_given = data['Password']
        user_given = data['User']
        if password_given != password_tr or user_given != user_tr:
            raise web.NotFound()
        
        # Get the apartment object, turn it into json and make the response
        web.header('Content-Type', 'application/json')
        apartment_copy = copy.deepcopy(apartment.get_dict())
        
        # Add the credentials to the message object
        apartment_copy['Password'] = password_tr
        apartment_copy['User'] = user_tr
        
        # Add the behavior information to the message object
        apartment_copy['lamp_movement'] = lamp_movement_reaction
        apartment_copy['no_movement_time'] = no_movement_interval
        
        apartment_copy['no_water_time'] = no_water_interval
        
        # Add the alarm information to the message object
        apartment_copy['alarm'] = alarms_all
        apartment_copy['alarmList'] = alarmList
        
        apartment_copy['alarm_urgent'] = alarms_urgend_all
        apartment_copy['alarmUrgentList'] = alarmsUrgentList
        
        json_apartment = json.dumps(apartment_copy)
        return json_apartment
    
    def POST(self):
        # get the posted json object and turn it into a dictionary
        json_request = web.data()
        post_dict = json.loads(json_request)
        
        # check the credentials stored in the json
        if 'Password' not in post_dict or 'User' not in post_dict:
            raise web.NotFound()
        password_given = post_dict['Password']
        user_given = post_dict['User']
        if password_given != password_tr or user_given != user_tr:
            raise web.NotFound()
        del post_dict['Password']
        del post_dict['User']
        
        # if the post object contains behavior information, update the values
        if 'lamp_movement' in post_dict:
            global no_movement_interval
            global lamp_movement_reaction
            no_movement_interval = int(post_dict['no_movement_time'])
            lamp_movement_reaction = post_dict['lamp_movement']
            
        global no_water_interval
        no_water_interval = post_dict['no_water_time']
            
        # adjust the state of both the real and the virtual apartment
        apartment.adjust_state(post_dict)
        if (not lamp_movement_reaction) and apartment.get_dev_status('Fedors_Zimmer', 'Lampe') == 'off':
            control.set_dev_state('Fedors_Zimmer', 'Lampe', 'off')
        # the reponse contains the current apartment state
        web.header('Content-Type', 'application/json')
        response = {'response' : 'success'}
        json_resp = json.dumps(response)
        return json_resp
        
        
        
if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
