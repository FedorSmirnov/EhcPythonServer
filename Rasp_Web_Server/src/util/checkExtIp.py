'''
Created on Jan 24, 2014

@author: fedor
'''

import subprocess
import threading
import urllib
import urllib2

current_ext_ip =''
ip_check_interval = 1800
webserver_ip_url = "http://hiwi.jochen-bauer.net/EhcServer/public/rasp/updateip"

def update_ext_ip(cur_ip):
    value = {"ip":cur_ip}
    data = urllib.urlencode(value)
    print urllib2.urlopen(webserver_ip_url, data).read()

def checkIP():
    global current_ext_ip
    resp_string = subprocess.check_output(['curl', '-s', 'icanhazip.com']).rstrip()
    
    
    if (current_ext_ip != resp_string):
        current_ext_ip = resp_string
        update_ext_ip(current_ext_ip)
    t = threading.Timer(ip_check_interval, checkIP)
    t.setDaemon(True)
    t.start()


    
