'''
Created on Jan 18, 2014

@author: fedor
'''
import local
import threading
import itertools

# defines all the things that are controlled by THIS raspberry
class Apartment:
    room_dict = None
    lock = None
    
    def __init__(self, init_dict):
        self.room_dict = init_dict
        self.lock = threading.Lock()
    
    def set_sens_state(self, room_name, sensor_name, sensor_state):
        for room in self.room_dict['rooms']:
            if room['name'] == room_name:
                for sensor in room['sensors']:
                    if sensor['name'] == sensor_name:
                        sensor['state'] = sensor_state
    
    def get_sens_status(self, room_name, sensor):
        for room in self.room_dict['rooms']:
            if room['name'] == room_name:
                for sens in room['sensors']:
                    if sens['name'] == sensor:
                        return sens['state'] 
    
    def get_dev_status(self, room_name, device_name):
        for room in self.room_dict['rooms']:
            if room['name'] == room_name:
                for device in room['devices']:
                    if device['name'] == device_name:
                        return device['state']
    
    def set_dev_state(self, room_name, device, state):
        for room in self.room_dict['rooms']:
            if room['name'] == room_name:
                for dev in room['devices']:
                    if dev['name'] == device:
                        dev['state'] = state
     
    def get_dict(self):
        return self.room_dict
    
    def get_lock(self):
        return self.lock
    
    # Function used to respond to act according to a device control request from the
    # web server or the mobile client 
    def adjust_state(self, state_dict):
        # Because we are working with multiple thread: lock the apartment variable 
        # before doing anything (not 100% sure whether this is necessary)
        self.lock.acquire()
        
        # Compare the two dictionaries and make adjustments, where necessary
        for room_want, room_is in itertools.product(state_dict['rooms'], self.room_dict['rooms']):
            if room_want['name'] == room_is['name']:
                dev_list_want = room_want['devices']
                dev_list_is = room_is['devices']
                for dev_is, dev_want in itertools.product(dev_list_is, dev_list_want):
                    if dev_is['name'] == dev_want['name'] and dev_is['state'] != dev_want['state']:
                        dev_is['state'] = dev_want['state']
                        local.rasp_to_fhem_comm.adjust_dev_state(room_is['name'], dev_is['name'], dev_is['state'])
               
        self.lock.release()
                    
                
    
    def to_string(self):
        return str (self.room_dict)
    
    

