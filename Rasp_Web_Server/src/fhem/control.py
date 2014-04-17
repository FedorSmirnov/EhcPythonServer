'''
Created on Jan 18, 2014

@author: fedor
'''
import subprocess
import constants
import urllib2
import re


def set_dev_state(room, device, state):
    
    cmd_ref = room + '.' + device
    
    if state == 'on':
        url = constants.get_on_url(cmd_ref)
    elif state == 'off':
        url = constants.get_off_url(cmd_ref)
    urllib2.urlopen(url)
    
# function to get a list with all devices and their status (not used at the moment)   
def get_dict(tec_name='CUL_HM:'):
    # get the list representing the state of the whole fhem
    process = subprocess.Popen(['/opt/fhem/fhem.pl', '%s:7072' % (constants.HOST), 'list'], stdout=subprocess.PIPE)
    resp_str = process.stdout.read()
    
    res = {}
    
    # Searching for all the switches
    switch_group = re.findall(r'(\w+)\.(\w+)\s+\((on|off)\)', resp_str)
    
    for switch in switch_group:
        room, device, state = switch
        
        if room not in res:
            res[room] = {}
        if 'devices' not in res[room]:
            res[room]['devices'] = {}
            
        res[room]['devices'][device] = state
     
    # Searching for the th-sensors
    
    th_sensor_group = re.findall(r'(\w+)\.\w+\s+\(\s*T:\s*(\d+\.\d)\s*H:\s*(\d+)\)', resp_str) 
    
    for th_sensor in th_sensor_group:
        room, temperature, humidity = th_sensor
        
        if room not in res:
            res[room] = {}
        if 'sensors' not in res[room]:
            res[room]['sensors'] = {} 
        res[room]['sensors']['temperature'] = temperature
        res[room]['sensors']['humidity'] = humidity
        
    # Searching for the door/window sensors
    
    door_sensor_group = re.findall(r'(\w+)\.(\w+)\s+\((open|closed)\)', resp_str)
    
    for door_sensor in door_sensor_group:
        room, door_name, door_state = door_sensor
        
        if room not in res:
            res[room] = {}
        if 'sensors' not in res[room]:
            res[room]['sensors'] = {}
        res[room]['sensors'][door_name] = door_state   
        
    # Searching for the water sensors
    
    water_sensor_group = re.findall(r'(\w+)\.(\w+)\s+\((dry|wet)\)', resp_str)
    
    for water_sensor in water_sensor_group:
        
        room, water_name, water_state = water_sensor
        if room not in res:
            res[room] = {}
        if 'sensors' not in res[room]:
            res[room]['sensors'] = {}
            
        res[room]['sensors'][water_name] = water_state
        
    
    # searching for all the motion sensors
    
    motion_sensors_group = re.findall(r'(\w+)\.(\w+)\s+\(\s*motion\s*\)', resp_str)
    
    for motion_sensor in motion_sensors_group:
        # not sure whether name is useful
        room, name = motion_sensor
    
        if room not in res:
            res[room] = {}
        if 'sensors' not in res[room]:
            res[room]['sensors'] = {} 
        
        res[room]['sensors']['motion'] = 'NONE'
        
    res_list = {"rooms":[]}    
    
    # turning dict into a list
    for room_name in res.keys():
        
        room_dict = {"name":room_name, "devices":[], "sensors":[]}
        if 'devices' in res[room_name]:
            for device_name in res[room_name]['devices']:
                dev_dict = {'name':device_name, 'state':res[room_name]['devices'][device_name]}
                room_dict['devices'].append(dev_dict)
        if 'sensors' in res[room_name]:        
            for sensor_name in res[room_name]['sensors']:
                sensor_dict = {'name':sensor_name, 'state':res[room_name]['sensors'][sensor_name]}
                room_dict['sensors'].append(sensor_dict)
                
        res_list["rooms"].append(room_dict)
                
    return res_list
    
