'''
Created on Jan 24, 2014

@author: fedor
'''

import subprocess
import threading
import re
import urllib
import urllib2

current_ext_ip =''
current_local_ip = ''
ip_check_interval = 1800
webserver_ip_url = "http://hiwi.jochen-bauer.net/EhcServer/public/rasp/updateip"

def update_ext_ip(cur_ex_ip, cur_loc_ip):
    value = {"ip":cur_ex_ip, "ip_local":cur_loc_ip}
    data = urllib.urlencode(value)
    print urllib2.urlopen(webserver_ip_url, data).read()

def checkIP():
    # check the external ip and update if necessary
    global current_ext_ip
    resp_string_ext = subprocess.check_output(['curl', '-s', 'icanhazip.com']).rstrip()
    
    global current_local_ip 
    resp_string_local_check = subprocess.check_output('ifconfig')
    resp_string_local = re.findall(r'wlan0\s*.+inet\s\w+:(\d+\.\d+\.\d+\.\d+)', resp_string_local_check, re.DOTALL)[0] 
    if (current_ext_ip != resp_string_ext or current_local_ip != resp_string_local):
        current_ext_ip = resp_string_ext
        current_local_ip = resp_string_local
        update_ext_ip(current_ext_ip, current_local_ip)
    t = threading.Timer(ip_check_interval, checkIP)
    t.setDaemon(True)
    t.start()


    
