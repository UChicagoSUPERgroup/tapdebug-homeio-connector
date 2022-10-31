from rule import TAPRule
from meta import MetaInfo
from device import Device
from traces import generate_trace_entry
from dev_monitor import monitor_status_change
from default_controller import apply_virtual_device_action, check_vdev_change

import time
import logging

motor_groups = {
    3: 4,
    4: 3,
    5: 6,
    6: 5,
    49: 50,
    50: 49,
    72: 73,
    73: 72,
    94: 95,
    95: 94,
    96: 97,
    97: 96,
    117: 118,
    118: 117,
    132: 133,
    133: 132,
    165: 166,
    166: 165,
    197: 198,
    198: 197,
    218: 219,
    219: 218,
    242: 243,
    243: 242,
}

def apply_action(dev: Device, val, meta_info: MetaInfo):
    # apply the action here
    # we should also update the status in this function 
    # and make a trace entry (is_automated=true)
    # we assume that actions triggered by a rule will 
    # not trigger other actions
    # this function should be guarded with status_lock and memory_map_lock
    if dev not in meta_info.virtual_dev_set:
        if meta_info.status.check_status(dev) != val:
            dev_instance = meta_info.get_funcs[dev.datatype](
                dev.address, meta_info.mem_types[dev.typ])

            if dev.address in motor_groups and dev.datatype == 'Bit' and val == True:
                # need to set the opposite engine to false
                opposite_instance = meta_info.get_funcs[dev.datatype](
                    motor_groups[dev.address], meta_info.mem_types[dev.typ])
                opposite_instance.Value = False
            
            dev_instance.Value = val
            meta_info.memory_map.Instance.Update()
            # update status
            meta_info.status.update_status(dev, val)
            # make trace
            time_val = meta_info.status.check_time()
            meta_info.trace.append(generate_trace_entry(dev, val, time_val, True))
            monitor_status_change(dev, val, meta_info)
            # check vdev change (if motor status changed for vdevs, reset automation mark)
            check_vdev_change(dev, val, meta_info)
    else:
        # this is an action sent to virtual device
        apply_virtual_device_action(dev, val, meta_info)


def trigger_rule(rule: TAPRule, meta_info: MetaInfo):
    # trigger the rule. This function assumes that the trigger is passed
    # we should apply the action immediately if conditions are met
    # this function should be guarded with meta_info.status_lock and memory_map_lock
    assert(meta_info.status_lock.locked(), "trigger_rule should be guarded with status_lock")
    assert(meta_info.memory_map_lock.locked(), "trigger_rule should be guarded with memory_map_lock")

    # check all conditions
    cond_sat = all([cond.check(cond.var, meta_info.status.check_status(
        cond.var)) for cond in rule.condition])
    if not cond_sat:
        return
    
    # apply the action
    meta_info.logger_rule.info('rule triggered: ' + str(rule.action.var) + ' ' + str(rule.action.val))
    apply_action(rule.action.var, rule.action.val, meta_info)
