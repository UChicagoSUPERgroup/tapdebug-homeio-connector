from typing import get_origin
import requests
import time
import logging

from meta import MetaInfo
from device import Device

typ_map = {
    'o': 'Output',
    'i': 'Input',
    'm': 'Memory'
}

datatype_map = {
    'b': 'Bit',
    'f': 'Float',
    'dt': 'DateTime'
}


def json_to_dev_set(response_json):
    dev_set = set()
    for dev_json in response_json['devs']:
        dev = Device(
            typ_map[dev_json['typ']], 
            datatype_map[dev_json['data_typ']], 
            int(dev_json['address']), 
            dev_json['name']
        )
        dev_set.add(dev)

    return dev_set


def init_device_monitors(global_meta_info: MetaInfo):
    data = {"token": global_meta_info.loc_token}
    response = requests.get(global_meta_info.monitored_dev_url, params=data)
    if response:
        dev_set = json_to_dev_set(response.json())
    else:
        global_meta_info.logger_monitor.info(response.status_code)
        return
    
    with global_meta_info.monitored_dev_lock:
        global_meta_info.monitored_devs = {key: None for key in dev_set}
        global_meta_info.logger_monitor.info('Devices monitored: ' + str(dev_set))


def monitor_status_change(dev, val, global_meta_info: MetaInfo):
    if dev in global_meta_info.monitored_devs:
        with global_meta_info.monitored_dev_lock:
            global_meta_info.monitored_devs[dev] = val
            global_meta_info.monitored_devs_updated = True


def generate_monitor_data(global_meta_info: MetaInfo):
    data = []
    for dev in global_meta_info.monitored_devs:
        val = global_meta_info.monitored_devs[dev]
        entry = {
            'dev_datatype': dev.datatype,
            'dev_typ': dev.typ,
            'dev_address': dev.address,
            'dev_name': dev.name,
            'val': val
        }
        data.append(entry)
    return data


def device_monitor(global_meta_info: MetaInfo):
    client = requests.session()
    response = client.get(global_meta_info.cookie_url)
    headers = {}
    headers['X-CSRFToken'] = response.cookies['csrftoken']
    while not global_meta_info.exit_flag:
        if global_meta_info.monitored_devs_updated:
            with global_meta_info.monitored_dev_lock:
                data = {'update': generate_monitor_data(global_meta_info), 'token': global_meta_info.loc_token}
                response = client.post(global_meta_info.update_monitor_url, json=data, headers=headers)
                global_meta_info.monitored_devs_updated = False
            global_meta_info.logger_monitor.info('device status sent')
        time.sleep(1)
    client.close()
