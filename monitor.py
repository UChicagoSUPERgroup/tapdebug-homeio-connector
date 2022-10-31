from device import Device
import time
import datetime
import threading
import copy

from rule import EventExpression
from meta import MetaInfo
from actuator import trigger_rule
from default_controller import trigger_default_controller, calc_virtual_device_status, \
    check_vdev_change, reset_motors
from traces import generate_trace_entry
from dev_monitor import monitor_status_change

def _to_datetime(datetime_orig, with_sec=False):
    return datetime.datetime(
        year=datetime_orig.Year, 
        month=datetime_orig.Month, 
        day=datetime_orig.Day, 
        hour=datetime_orig.Hour, 
        minute=datetime_orig.Minute,
        second=datetime_orig.Second if with_sec else 0)

def _trigger_rule(global_meta_info, time_val, dev, val, old_val=None):
    with global_meta_info.rule_lock:
        event = EventExpression(dev, '=', val)
        for rule_id in range(len(global_meta_info.rule_list)):
            rule = global_meta_info.rule_list[rule_id]
            if rule.is_hold():
                if rule.trigger_e.var == dev:
                    if old_val is None:
                        should_schedule = rule.trigger_e.check(event)
                    else:
                        old_event = EventExpression(dev, '=', old_val)
                        should_schedule = rule.trigger_e.check(event) and not rule.trigger_e.check(old_event)
                    if should_schedule:  # should schedule the rule
                        target_time = time_val + datetime.timedelta(seconds=rule.trigger_e.hold_t)
                        global_meta_info.rule_scheduled[rule_id] = target_time
                    else:  # should cancel the scheduled rule
                        if rule_id in global_meta_info.rule_scheduled:
                            del global_meta_info.rule_scheduled[rule_id]
            else:
                if old_val is None:
                    if rule.trigger_e.check(event):
                        trigger_rule(rule, global_meta_info)
                else:
                    old_event = EventExpression(dev, '=', old_val)
                    if rule.trigger_e.check(event) and not rule.trigger_e.check(old_event):
                        trigger_rule(rule, global_meta_info)

def check_value_change(global_meta_info: MetaInfo, dry_run=False):
    with global_meta_info.memory_map_lock:
        global_meta_info.memory_map.Instance.Update()

        # time change
        time_val = global_meta_info.get_funcs['DateTime'](
            global_meta_info.datetime_addr, global_meta_info.memory_type.Memory).Value
        time_val = _to_datetime(time_val, True)
        old_time_val = global_meta_info.status.check_time()
        time_changed = False
        if time_val != old_time_val and not dry_run:
            # time changed, should update status
            global_meta_info.status.update_time(time_val)
            # Then trigger rules if needed according to this flag
            time_changed = True
        
        # device value changes
        with global_meta_info.status_lock:
            # trigger regular rules (without timing)
            for dev in global_meta_info.dev_list:
                if dev.datatype == 'DateTime':
                    continue
                val = global_meta_info.get_funcs[dev.datatype](
                    dev.address, global_meta_info.mem_types[dev.typ]).Value
                if not global_meta_info.status.compare_status(dev, val) and not dry_run:
                    # get the old status
                    old_val = global_meta_info.status.check_status(dev)
                    # value changed, should update status
                    update_id = global_meta_info.status.update_status(dev, val)
                    # should store trace
                    global_meta_info.trace.append(generate_trace_entry(dev, val, time_val))
                    # update monitored devices' status
                    monitor_status_change(dev, val, global_meta_info)
                    # check vdev change (if motor status changed for vdevs, reset automation mark)
                    check_vdev_change(dev, val, global_meta_info)
                    # trigger default controllers
                    trigger_default_controller(dev, val, global_meta_info)
                    # need to reset the motors once change finished
                    reset_motors(dev, val, global_meta_info)
                    # then trigger rules if needed
                    _trigger_rule(global_meta_info, time_val, dev, val, old_val)
            # update virtual devices' status
            for dev in global_meta_info.virtual_dev_list:
                val = calc_virtual_device_status(dev, global_meta_info.status)
                if not global_meta_info.status.compare_status(dev, val) and not dry_run:
                    # get the old status
                    old_val = global_meta_info.status.check_status(dev)
                    # value changed, should update status
                    update_id = global_meta_info.status.update_status(dev, val)
                    # should store trace, need to check if it is an automated action
                    is_automated = False
                    if dev in global_meta_info.virtual_dev_auto_mark:
                        automation_val = global_meta_info.virtual_dev_auto_mark[dev]
                        if val == automation_val:
                            is_automated = True
                        del global_meta_info.virtual_dev_auto_mark[dev]
                    global_meta_info.trace.append(generate_trace_entry(dev, val, time_val, is_automated))
                    # update monitored devices' status
                    monitor_status_change(dev, val, global_meta_info)
                    # then trigger rules if needed
                    _trigger_rule(global_meta_info, time_val, dev, val, old_val)
            
            # trigger clock rules (if it becomes xx:xx)
            if time_changed:
                with global_meta_info.rule_lock:
                    if old_time_val is not None and \
                       time_val > old_time_val and \
                       time_val-old_time_val < datetime.timedelta(minutes=5):
                        curr_time = old_time_val.replace(second=0)
                        while curr_time <= time_val:
                            if curr_time > old_time_val:
                                # only trigger once per minute
                                hour_minute = curr_time.strftime('%H:%M')
                                time_dev = Device('Memory', 'DateTime', 65, '')
                                event = EventExpression(time_dev, '=', hour_minute)
                                for rule in global_meta_info.rule_list:
                                    if rule.is_clock():
                                        if rule.trigger_e.check(event):
                                            trigger_rule(rule, global_meta_info)
                            curr_time += datetime.timedelta(minutes=1)

            # trigger holding rules (if xxx has been true for xx time)
            if time_changed:
                with global_meta_info.rule_lock:
                    to_delete = []
                    for rule_id in global_meta_info.rule_scheduled:
                        if time_val >= global_meta_info.rule_scheduled[rule_id]:
                            rule = global_meta_info.rule_list[rule_id]
                            trigger_rule(rule, global_meta_info)
                            to_delete.append(rule_id)
                    for rule_id in to_delete:
                        del global_meta_info.rule_scheduled[rule_id]


def monitor(global_meta_info: MetaInfo):
    # on_input_value_changed = ValueChangeHandler(global_meta_info)
    # global_meta_info.memory_map.Instance.InputsValueChanged += \
    #     global_meta_info.memories_changed_event_handler(
    #         on_input_value_changed)
    round = 0
    while not global_meta_info.exit_flag:
        # global_meta_info.memory_map_lock.acquire()
        # global_meta_info.memory_map.Instance.Update()
        if round < global_meta_info.dry_run_rounds:
            check_value_change(global_meta_info, True)
            round = round + 1
        else:
            check_value_change(global_meta_info)
        # global_meta_info.memory_map_lock.release()
        time.sleep(16/1000)
