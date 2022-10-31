import time
from typing import get_origin
import requests
import copy
import logging

from meta import MetaInfo
from device import Device
from rule import TAPRule, TriggerExpression, ConditionExpression, ActionExpression

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


# Translate json rules from backend to TAPRules
def json_to_rule_list(response_json):
    rule_list = []
    for rule_json in response_json['rules']:
        trigger_dev = Device(
            typ_map[rule_json['trigger']['dev']['typ']], 
            datatype_map[rule_json['trigger']['dev']['data_typ']], 
            int(rule_json['trigger']['dev']['address']), 
            rule_json['trigger']['dev']['name']
        )
        trigger_comp =  rule_json['trigger']['comp']
        trigger_val = rule_json['trigger']['val']
        hold_t = rule_json['trigger']['hold_t']

        trigger = TriggerExpression(trigger_dev, trigger_comp, trigger_val, hold_t=hold_t)

        conditions = []
        for cond in rule_json['conditions']:
            condition_dev = Device(
                typ_map[cond['dev']['typ']], 
                datatype_map[cond['dev']['data_typ']], 
                int(cond['dev']['address']), 
                cond['dev']['name']
            )
            condition_comp = cond['comp']
            condition_val = cond['val']
            conditions.append(ConditionExpression(condition_dev, condition_comp, condition_val))
        
        action_dev = Device(
            typ_map[rule_json['action']['dev']['typ']], 
            datatype_map[rule_json['action']['dev']['data_typ']], 
            int(rule_json['action']['dev']['address']), 
            rule_json['action']['dev']['name']
        )
        action_comp = rule_json['action']['comp']
        action_val = rule_json['action']['val']
        action = ActionExpression(action_dev, action_comp, action_val)

        rule_list.append(TAPRule(trigger, conditions, action))

    return rule_list


# Translate backend devs to Devices
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


###################################################
# upload the traces onto the server
# called from backend_monitor
###################################################
def upload_traces(meta_info: MetaInfo):
    meta_info.logger_trace.info('Upload started. ')
    try:
        client = requests.session()

        response = client.get(meta_info.cookie_url)
        headers = {}
        headers['X-CSRFToken'] = response.cookies['csrftoken']

        # we do not delete the trace itself in case the upload is not successful
        trace = copy.deepcopy(meta_info.trace)
        total_num = len(trace)
        current_num = 0
        cache_token = ''
        while trace:
            if len(trace) > meta_info.upload_batchsize:
                data = {'trace': trace[:meta_info.upload_batchsize], 'token': meta_info.loc_token, 'last': False, 'cache_token': cache_token}
                trace = trace[meta_info.upload_batchsize:]
                current_num += meta_info.upload_batchsize
            else:
                data = {'trace': trace, 'token': meta_info.loc_token, 'last': True, 'cache_token': cache_token}
                trace = []
            response = client.post(meta_info.trace_url, json=data, headers=headers)
            meta_info.logger_trace.info('Uploading... %d/%d' % (current_num, total_num))
            cache_token = response.json()['cache_token']
            if response.status_code != 200:
                meta_info.logger_trace.warning('Trace has not been successfully uploaded, status_code: ' + str(response.status_code))
                break

        client.close()
    except Exception as exc:
        meta_info.logger_trace.error('Upload terminated. ')
        meta_info.logger_trace.error(str(exc))
    else:
        meta_info.logger_trace.info('Upload succeeded. ')


######## monitor the backend for update on rules and device monitors ########
def rule_dev_monitor(global_meta_info: MetaInfo):
    data = {"user_code": global_meta_info.user_code}
    while not global_meta_info.exit_flag:
        response = requests.get(global_meta_info.rule_dev_url, params=data)
        response_json = response.json()
        if response:
            rule_list = json_to_rule_list(response_json)
            dev_set = json_to_dev_set(response_json)
        else:
            raise Exception("Connection to backend failed: ", response.status_code)

        # update location token
        if response_json["loc_token"] != global_meta_info.loc_token:
            global_meta_info.loc_token = response_json["loc_token"]
        
        # upload trace if needed
        if response_json["loc_token"] == global_meta_info.loc_token and response_json["pending_trace"]:
            upload_traces(global_meta_info)
        
        # update rules
        if rule_list != global_meta_info.rule_list:
            with global_meta_info.rule_lock:
                global_meta_info.rule_list = rule_list
                with global_meta_info.status_lock:
                    # we clear the scheduled rules once rule list changes
                    global_meta_info.rule_scheduled = dict()
            global_meta_info.logger_rule.info('rule changed')
            global_meta_info.logger_rule.info(str(rule_list))
        
        # update devs
        # currently disabled since we do not need to monitor devices during the interview
        # monitored_devs = {key: None for key in dev_set}
        # if monitored_devs != global_meta_info.monitored_devs:
        #     with global_meta_info.monitored_dev_lock:
        #         global_meta_info.monitored_devs = monitored_devs
        #     print('Devices monitored: ', dev_set)
        
        time.sleep(2)


######## send device status to backend ########
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


def status_update_to_backend(global_meta_info: MetaInfo):
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