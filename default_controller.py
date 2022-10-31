from device import Device
from meta import MetaInfo
from status import Status
from traces import generate_trace_entry
from dev_monitor import monitor_status_change

import math


###################################################
# SS: single-single controller
# a single switch controlling a binary output (flip)
###################################################
ss_controller_map = {
    0: [187],
    1: [188, 189],
    2: [41],
    27: [19],
    28: [20],
    39: [30],
    67: [54],
    68: [41],
    69: [174],
    70: [191],
    71: [190],
    93: [68],
    112: [83],
    113: [83],
    114: [83],
    115: [83],
    116: [83],
    130: [97],
    131: [97],
    150: [110],
    163: [122],
    164: [122],
    195: [146],
    196: [146],
    217: [159],
    233: [172],
    234: [172],
    235: [172],
}

###################################################
# SS: single-single controller (direct)
# a single switch controlling a binary output (same status)
###################################################
ssd_controller_map = {
    92: [69],
}

###################################################
# DS: double-single controller
# two switches controlling a binary output
###################################################
ds_controller_map = {
    (7, 8): [0],
    (9, 10): [0],
    (11, 12): [0],
    (51, 52): [40],
    (53, 54): [40],
    (74, 75): [54],
    (76, 77): [54],
    (134, 135): [97],
    (151, 152): [111],
    (167, 168): [122],
    (183, 184): [135],
    (199, 200): [146],
    (201, 202): [146],
    (236, 237): [173],
    (238, 239): [173],
    (240, 241): [174],
    (274, 275): [58]
}

ds_controller_group = {
    7: (7, 8),
    8: (7, 8),
    9: (9, 10),
    10: (9, 10),
    11: (11, 12),
    12: (11, 12),
    51: (51, 52),
    52: (51, 52),
    53: (53, 54),
    54: (53, 54),
    74: (74, 75),
    75: (74, 75),
    76: (76, 77),
    77: (76, 77),
    134: (134, 135),
    135: (134, 135),
    151: (151, 152),
    152: (151, 152),
    167: (167, 168),
    168: (167, 168),
    183: (183, 184),
    184: (183, 184),
    199: (199, 200),
    200: (199, 200),
    201: (201, 202),
    202: (201, 202),
    236: (236, 237),
    237: (236, 237),
    238: (238, 239),
    239: (238, 239),
    240: (240, 241),
    241: (240, 241),
    274: (274, 275),
    275: (274, 275)
}

###################################################
# DD: double-double controller
# two switches controlling two outputs
###################################################
dd_controller_map = {
    (3, 4): [(1, 2), (3, 4)],
    (5, 6): [(5, 6), (7, 8)],
    (49, 50): [(42, 43)],
    (72, 73): [(55, 56)],
    (94, 95): [(72, 73)],
    (96, 97): [(70, 71)],
    (117, 118): [(84, 85)],
    (132, 133): [(98, 99)],
    (165, 166): [(123, 124)],
    (197, 198): [(147, 148)],
    (218, 219): [(160, 161)],
    (242, 243): [(175, 176)],
    (276, 277): [(72, 73)],
    (278, 279): [(193, 194)]
}

dd_controller_group = {
    3: (3, 4),
    4: (3, 4),
    5: (5, 6),
    6: (5, 6),
    49: (49, 50),
    50: (49, 50),
    72: (72, 73),
    73: (72, 73),
    94: (94, 95),
    95: (94, 95),
    96: (96, 97),
    97: (96, 97),
    117: (117, 118),
    118: (117, 118),
    132: (132, 133),
    133: (132, 133),
    165: (165, 166),
    166: (165, 166),
    197: (197, 198),
    198: (197, 198),
    218: (218, 219),
    219: (218, 219),
    242: (242, 243),
    243: (242, 243),
    276: (276, 277),
    277: (276, 277),
    278: (278, 279),
    279: (278, 279)
}

###################################################
# Reverse map for shade-like virtual devices
# this dict map virtual dev id to the openness id
###################################################
shade_ids = {
    1000, 
    1001, 
    1002, 
    1003, 
    1004, 
    1005, 
    1006, 
    1007, 
    1008, 
    1009, 
    1010, 
    1011, 
    1012,
}
shade_openness_map = {
    1000: 3,
    1001: 4,
    1002: 5,
    1003: 6,
    1004: 15,
    1005: 27,
    1006: 37,
    1007: 48, 
    1008: 60,
    1009: 83,
    1010: 106,
    1011: 118,
    1012: 130,
}
shade_openness_rev_map = {
    3: 1000,
    4: 1001,
    5: 1002,
    6: 1003,
    15: 1004,
    27: 1005,
    37: 1006,
    48: 1007,
    60: 1008,
    83: 1009,
    106: 1010,
    118: 1011,
    130: 1012
}
shade_motor_map = {
    1000: (1, 2),
    1001: (3, 4),
    1002: (5, 6),
    1003: (7, 8),
    1004: (42, 43),
    1005: (55, 56),
    1006: (70, 71),
    1007: (84, 85), 
    1008: (98, 99),
    1009: (123, 124),
    1010: (147, 148),
    1011: (160, 161),
    1012: (175, 176),
}

###################################################
# Reverse map for garage-door-like virtual devices
# this dict map virtual dev id to the closed id
###################################################
garage_door_ids = {
    1013,
    1014,
}
garage_door_closed_map = {
    1013: 101,
    1014: 261,
}
garage_door_motor_map = {
    1013: (72, 73),
    1014: (193, 194),
}
garage_door_closed_rev_map = {
    101: 1013,
    261: 1014
}
garage_door_opened_rev_map = {
    100: 1013,
    260: 1014
}

###################################################
# Reverse map for the alarm key pad
# this dict map virtual dev id to the armed id
###################################################
alarm_key_pad_ids = {
    1015
}
alarm_key_pad_armed_map = {
    1015: 82
}
alarm_key_pad_motor_map = {
    1015: (59, 60)
}
alarm_key_pad_armed_rev_map = {
    82: 1015
}

###################################################
# Map motors to their vdevs
###################################################
motor_vdev_map = {
    1: 1000,
    2: 1000,
    3: 1001,
    4: 1001,
    5: 1002,
    6: 1002,
    7: 1003,
    8: 1003,
    42: 1004,
    43: 1004,
    55: 1005,
    56: 1005,
    70: 1006,
    71: 1006,
    84: 1007,
    85: 1007,
    98: 1008,
    99: 1008,
    123: 1009,
    124: 1009,
    147: 1010,
    148: 1010,
    160: 1011,
    161: 1011,
    175: 1012,
    176: 1012,
    72: 1013,
    73: 1013,
    193: 1014,
    194: 1014,
    59: 1015,
    60: 1015
}


###################################################
# check if a default controller is triggered
# this should be called when status and memory map are locked
###################################################
def check_default_controller(dev: Device, val, meta_info: MetaInfo):
    actions_list = []
    if dev.typ == 'Input' and dev.datatype == 'Bit' and val == True:
        if dev.address in ss_controller_map:
            for target_addr in ss_controller_map[dev.address]:
                target_dev = Device('Output', 'Bit', target_addr, '')
                curr_target_status = meta_info.status.check_status(target_dev)
                actions_list.append((target_dev, not curr_target_status))
        elif dev.address in ssd_controller_map:
            for target_addr in ssd_controller_map[dev.address]:
                target_dev = Device('Output', 'Bit', target_addr, '')
                actions_list.append((target_dev, True))
        elif dev.address in ds_controller_group:
            group = ds_controller_group[dev.address]
            for target_addr in ds_controller_map[group]:
                target_dev = Device('Output', 'Bit', target_addr, '')
                # target should be true if it's the "UP" button and false o/w.
                target_status = dev.address == group[0]
                actions_list.append((target_dev, target_status))
        elif dev.address in dd_controller_group:
            group = dd_controller_group[dev.address]
            for target_group in dd_controller_map[group]:
                target_dev0 = Device('Output', 'Bit', target_group[0], '')
                target_dev1 = Device('Output', 'Bit', target_group[1], '')
                curr_target_status0 = meta_info.status.check_status(target_dev0)
                curr_target_status1 = meta_info.status.check_status(target_dev1)
                if dev.address == group[0]:
                    if not curr_target_status0 and not curr_target_status1:
                        actions_list.append((target_dev0, True))
                    elif not curr_target_status0 and curr_target_status1:
                        actions_list.append((target_dev1, False))
                    elif curr_target_status0 and curr_target_status1:
                        actions_list.append((target_dev1, False))
                    else:
                        pass
                else:
                    if not curr_target_status0 and not curr_target_status1:
                        actions_list.append((target_dev1, True))
                    elif curr_target_status0 and not curr_target_status1:
                        actions_list.append((target_dev0, False))
                    elif curr_target_status0 and curr_target_status1:
                        actions_list.append((target_dev0, False))
                    else:
                        pass
        else:
            pass
    elif dev.typ == 'Input' and dev.datatype == 'Bit' and val == False:
        if dev.address in ssd_controller_map:
            for target_addr in ssd_controller_map[dev.address]:
                target_dev = Device('Output', 'Bit', target_addr, '')
                actions_list.append((target_dev, False))
        else:
            pass
    return actions_list


###################################################
# trigger actions from default controllers
# this should be called when status and memory map are locked
###################################################
def trigger_default_controller(dev: Device, val, meta_info: MetaInfo):
    # get actions that are triggered
    actions_list = check_default_controller(dev, val, meta_info)
    # apply those actions
    for dev, target_val in actions_list:
        dev_instance = meta_info.get_funcs[dev.datatype](
            dev.address, meta_info.mem_types[dev.typ])
        dev_instance.Value = target_val

###################################################
# when vdev finishs a status change
# we should stop both motors
# This shouldn't be considered a "manual change"
# to avoid inconsistency.
# Manual change is tracked by remote buttons
###################################################
def reset_motors(dev: Device, val, meta_info: MetaInfo):
    if dev.typ == 'Input':
        if dev.datatype == 'Float' and dev.address in shade_openness_rev_map:
            vdev_addr = shade_openness_rev_map[dev.address]
            if math.floor(val * 10) == 0 or math.ceil(val * 100) == 1000:
                motors = list(shade_motor_map[vdev_addr])
            else:
                motors = []
        elif dev.datatype == 'Bit' and dev.address in garage_door_opened_rev_map:
            vdev_addr = garage_door_opened_rev_map[dev.address]
            motors = list(garage_door_motor_map[vdev_addr]) if val else []
        elif dev.datatype == 'Bit' and dev.address in garage_door_closed_rev_map:
            vdev_addr = garage_door_closed_rev_map[dev.address]
            motors = list(garage_door_motor_map[vdev_addr]) if val else []
        elif dev.datatype == 'Bit' and dev.address in alarm_key_pad_armed_rev_map:
            vdev_addr = alarm_key_pad_armed_rev_map[dev.address]
            motors = list(alarm_key_pad_motor_map[vdev_addr])  # this happened immediately. Should reset both
        else:
            motors = []

        for motor_addr in motors:
            motor_dev = Device('Output', 'Bit', motor_addr, '')
            motor_instance = meta_info.get_funcs[motor_dev.datatype](
                motor_dev.address, meta_info.mem_types[motor_dev.typ])
            motor_instance.Value = False


###################################################
# check motor change for virtual devices
# if status changed in the opposite way, 
# we need to reset the automation mark
# this should be called when status and memory map are locked
# TODO: we should check the button instead of the motor
# to avoid inconsistency in automation
###################################################
def check_vdev_change(dev, val, meta_info: MetaInfo):
    if dev.typ == 'Input' and dev.datatype == 'Bit' and dev.address in dd_controller_group and val:
        # it is only possible to revert shade automation (under dd controller group)
        # we do not believe users can revert alarm pad automation since it happens instantaneously
        switch_group = dd_controller_group[dev.address]
        motor_groups = dd_controller_map[switch_group]
        for motor_group in motor_groups:
            target_motor = motor_group[0] if dev.address == switch_group[0] else motor_group[1]
            vdev_address = motor_vdev_map[target_motor]
            if vdev_address in shade_motor_map:
                up_motor, _ = shade_motor_map[vdev_address]
            elif vdev_address in garage_door_motor_map:
                up_motor, _ = garage_door_motor_map[vdev_address]
            elif vdev_address in alarm_key_pad_motor_map:
                up_motor, _ = alarm_key_pad_motor_map[vdev_address]
            else:
                return
            vdev = Device('Output', 'Bit', vdev_address, '')
            if vdev in meta_info.virtual_dev_auto_mark:
                target_val = meta_info.virtual_dev_auto_mark[vdev]
                if target_val != (target_motor == up_motor) and vdev_address not in alarm_key_pad_ids:
                    # if the target value of automation does not match the command sent by users,
                    # delete the automation mark
                    del meta_info.virtual_dev_auto_mark[vdev]


###################################################
# calculate the correct virtual device status
# this should be called when status and memory map are locked
###################################################
def calc_virtual_device_status(dev: Device, status: Status):
    if dev.address in shade_ids:
        openness_id = shade_openness_map[dev.address]
        openness_dev = Device('Input', 'Float', openness_id, '')
        openness = status.check_status(openness_dev)
        return openness is not None and math.floor(openness * 10) != 0
    elif dev.address in garage_door_ids:
        closed_id = garage_door_closed_map[dev.address]
        closed_dev = Device('Input', 'Bit', closed_id, '')
        closed = status.check_status(closed_dev)
        return closed is not None and not closed
    elif dev.address in alarm_key_pad_ids:
        armed_id = alarm_key_pad_armed_map[dev.address]
        armed_dev = Device('Input', 'Bit', armed_id, '')
        armed = status.check_status(armed_dev)
        return armed is not None and armed
    else:
        raise Exception("the device with address %d is not found." % dev.address)


###################################################
# apply an action to virtual device
# this should be called when status and memory map are locked
###################################################
def apply_virtual_device_action(dev: Device, val, meta_info: MetaInfo):
    if dev.address in shade_ids:
        open_dev_id, close_dev_id = shade_motor_map[dev.address]
    elif dev.address in garage_door_ids:
        open_dev_id, close_dev_id = garage_door_motor_map[dev.address]
    elif dev.address in alarm_key_pad_ids:
        open_dev_id, close_dev_id = alarm_key_pad_motor_map[dev.address]
    else:
        raise Exception("the device with address %d is not found." % dev.address)
    
    open_dev = Device('Output', 'Bit', open_dev_id, '')
    close_dev = Device('Output', 'Bit', close_dev_id, '')
    open_motor_instance = meta_info.get_funcs[open_dev.datatype](
        open_dev.address, meta_info.mem_types[open_dev.typ])
    close_motor_instance = meta_info.get_funcs[close_dev.datatype](
        close_dev.address, meta_info.mem_types[close_dev.typ])
    
    # turn on one motor and stop the opposite one
    open_motor_instance.Value = val
    close_motor_instance.Value = not val

    # update status in memory and status in Status
    meta_info.memory_map.Instance.Update()
    meta_info.status.update_status(open_dev, val)
    meta_info.status.update_status(close_dev, not val)

    # create trace log
    time_val = meta_info.status.check_time()
    meta_info.trace.append(generate_trace_entry(open_dev, val, time_val, True))
    meta_info.trace.append(generate_trace_entry(close_dev, not val, time_val, True))
    monitor_status_change(open_dev, val, meta_info)
    monitor_status_change(close_dev, not val, meta_info)

    # we need to mark that this action is automated, not only for the motors,
    # but the v device as well. The virtual device's action might happen several 
    # seconds after this action
    meta_info.virtual_dev_auto_mark[dev] = val
