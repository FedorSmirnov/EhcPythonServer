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

# local imports
from local import rasp_to_fhem_comm
from util import checkExtIp
from fhem import constants


# mapping of the URLs to the controller classes
urls = ('/', 'index', '/handshake', 'handshake')

# credentials (perhaps good idea to add encryption later)
password_tr = 'geheim'
user_tr = 'guest@jochen-bauer.net'

# get your own external IP and report it to the web server (periodically repeated in an extra thread)
checkExtIp.checkIP()

# init of the object representing the state of all controlled devices
apartment = rasp_to_fhem_comm.init()

# function used for the event listening
def listen_to_events():
    tn = telnetlib.Telnet(constants.HOST, constants.PORT_TELNET)
    tn.write('inform timer\n')
    index, match_object, text = tn.expect(constants.REG_LIST)
    tn.write('exit\n')
    time = match_object.group(1)
    room = match_object.group(2) 
    dev_name = match_object.group(3)
    apartment.get_lock().acquire()
    if index == 0:
        # Event caused by a motion detector
        apartment.set_sens_state(room, 'motion', time)
    if index == 1:
        # Event caused by a temperature/humidity sensor  
        temp = match_object.group(4)
        humid = match_object.group(5)
        apartment.set_sens_state(room, 'temperature', temp)
        apartment.set_sens_state(room, 'humidity', humid)
    if index == 2:
        # Event caused by a switch
        state = match_object.group(4)
        apartment.set_dev_state(room, dev_name, state)
    if index == 3:
        # Event caused by a door sensor
        state = match_object.group(4)
        apartment.set_sens_state(room, dev_name, state)
    if index == 4:
        # Event caused by a water sensor
        state = match_object.group(4)
        apartment.set_sens_state(room, dev_name, state)
        
    apartment.get_lock().release()
    tn.close()
    # When finished with the reading, the function calls itself in a new thread to keep listening
    thread_timer = threading.Timer(0, listen_to_events)
    thread_timer.setDaemon(True)
    thread_timer.start()    



# start the thread listening for the fhem events
listen_to_events()

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
        apartment_copy['Password'] = password_tr
        apartment_copy['User'] = user_tr
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
        
        # adjust the state of both the real and the virtual apartment
        apartment.adjust_state(post_dict)
        # the reponse contains the current apartment state
        web.header('Content-Type','application/json')
        response = {'response' : 'success'}
        json_resp = json.dumps(response)
        return json_resp
        
        
        
if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
