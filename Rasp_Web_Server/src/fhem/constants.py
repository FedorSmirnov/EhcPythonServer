'''
Created on Jan 18, 2014

@author: fedor
'''
import subprocess
from compiler.ast import Sub

HOST = '192.168.178.32'
PORT_TELNET = '7072'

regex_list = []
regex_motion = r'(\d+-\d+-\d+\s\d+:\d+:\d+)\sCUL_HM\s(\w+)\.(\w+)\smotion'
regex_temp_and_humid = r'(\d+-\d+-\d+\s\d+:\d+:\d+)\sCUL_HM\s(\w+)\.(\w+)\sT:\s(\d+\.\d+)\sH:\s(\d+)'
regex_switch = r'(\d+-\d+-\d+\s\d+:\d+:\d+)\sCUL_HM\s(\w+)\.(\w+)\s(on|off)'
regex_door = r'(\d+-\d+-\d+\s\d+:\d+:\d+)\sCUL_HM\s(\w+)\.(\w+)\s(open|closed)'
regex_water = r'(\d+-\d+-\d+\s\d+:\d+:\d+)\sCUL_HM\s(\w+)\.(\w+)\s(wet|dry)'
regex_list.append(regex_motion)
regex_list.append(regex_temp_and_humid)
regex_list.append(regex_switch)
regex_list.append(regex_door)
regex_list.append(regex_water)

REG_LIST = regex_list

URL_BASE = 'http://%s:8083/fhem?' % HOST


#def get_fhem_cmd_string_list(cmd_name):
#    return ['perl', '/opt/fhem/fhem.pl', '%s:7072'%(HOST), '"%s"'%(cmd_name)]

def get_cmd_url(dev_name, cmd_name):
    return URL_BASE +  'cmd.' + dev_name + '=set%20'+dev_name+'%20'+cmd_name+'&amp;room=CUL_HM' 

def get_toggle_url(dev_name):
    return get_cmd_url(dev_name, 'toggle')

def get_on_url(dev_name):
    return get_cmd_url(dev_name, 'on')

def get_off_url(dev_name):
    return get_cmd_url(dev_name,  'off')

def get_statusRequest_url(dev_name):
    return get_cmd_url(dev_name,  'statusRequest')



