from typing import List, Dict, Any, Tuple
import math

from device import Device

class Status(object):
    def __init__(self, device_list: List[Device], virtual_device_list: List[Device]):
        # track status of regular devices
        self.device_status = {dev: None for dev in device_list}
        self.last_updated = {dev: None for dev in device_list}
        self.update_id = {dev: 0 for dev in device_list}
        # track status of high-level virtual devices like 
        # boolean shades/garage doors
        self.v_device_status = {dev: None for dev in virtual_device_list}
        self.v_last_updated = {dev: None for dev in virtual_device_list}
        self.v_update_id = {dev: 0 for dev in virtual_device_list}
        # track time
        self.time = None
    
    def check_status(self, dev: Device):
        if dev in self.device_status:
            return self.device_status[dev]
        elif dev in self.v_device_status:
            return self.v_device_status[dev]
        else:
            raise Exception("the device with address %d is not found." % dev.address)
    
    def compare_status(self, dev: Device, val):
        if dev in self.device_status:
            current_val = self.device_status[dev]
        elif dev in self.v_device_status:
            current_val = self.v_device_status[dev]
        else:
            raise Exception("the device with address %d is not found." % dev.address)
        if dev.datatype == 'Float' and current_val is not None:
            return math.floor(val * 10) == math.floor(current_val * 10)
        else:
            return val == current_val

    def update_status(self, dev: Device, val):
        if dev in self.device_status:
            self.device_status[dev] = val
            self.last_updated[dev] = self.time
            update_id = (self.update_id[dev] + 1) % 1048576
            self.update_id[dev] = update_id
        elif dev in self.v_device_status:
            self.v_device_status[dev] = val
            self.v_last_updated[dev] = self.time
            update_id = (self.v_update_id[dev] + 1) % 1048576
            self.v_update_id[dev] = update_id
        else:
            raise Exception("the device with address %d is not found." % dev.address)
        return update_id

    def check_update_time_and_id(self, dev):
        if dev in self.device_status:
            return self.last_updated[dev], self.update_id[dev]
        elif dev in self.v_device_status:
            return self.v_last_updated[dev], self.v_update_id[dev]
        else:
            raise Exception("the device with address %d is not found." % dev.address)
    
    def check_time(self):
        return self.time

    def update_time(self, time):
        self.time = time
