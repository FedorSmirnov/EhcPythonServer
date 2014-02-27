'''
Created on Jan 18, 2014

@author: fedor
'''

from model.entities import Apartment
import fhem.control

def init():
    init_dict = fhem.control.get_dict()
    apartment = Apartment(init_dict)
    return apartment


def adjust_dev_state(room, device, new_state):
    fhem.control.set_dev_state(room, device, new_state)