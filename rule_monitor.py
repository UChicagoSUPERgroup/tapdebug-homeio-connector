import time
from typing import get_origin
import requests
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



def rule_monitor(global_meta_info: MetaInfo):
    data = {"user_code": global_meta_info.user_code}
    response = requests.get(global_meta_info.rule_url, params=data)
    if response:
        rule_list = json_to_rule_list(response.json())
    else:
        global_meta_info.logger_rule.warning('rule fetching failed, status_code: ' + str(response.status_code))

    if rule_list != global_meta_info.rule_list:
        with global_meta_info.rule_lock:
            global_meta_info.rule_list = rule_list
            with global_meta_info.status_lock:
                # we clear the scheduled rules once rule list changes
                global_meta_info.rule_scheduled = dict()
        global_meta_info.logger_rule.info('rule changed')
        global_meta_info.logger_rule.info(str(rule_list))