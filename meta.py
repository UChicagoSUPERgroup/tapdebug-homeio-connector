import threading
import logging

from status import Status

class MetaInfo(object):
    def __init__(self, memory_map, memory_type, memories_changed_event_handler, 
                 dev_list, virtual_dev_list, rule_list, user_code, server_url):
        
        ### Objects to communicate with Home I/O ###
        # When used, should guard with memory_map_lock
        self.memory_map = memory_map
        self.memory_type = memory_type
        self.memories_changed_event_handler = memories_changed_event_handler
        self.memory_map_lock = threading.Lock()

        ### List of devices (static) ###
        self.dev_list = dev_list
        # List of virtual devices (those are high-level devices 
        # abstracted from shades/garage doors)
        self.virtual_dev_list = virtual_dev_list
        self.virtual_dev_set = set(virtual_dev_list)

        ### List of TAP rules ###
        # When used, should guard with rule_lock
        self.rule_list = rule_list
        self.rule_lock = threading.Lock()

        ### List of monitored devices ###
        # When used, should guard with monitored_dev_lock
        self.monitored_devs = dict()
        self.monitored_devs_updated = False
        self.monitored_dev_lock = threading.Lock()

        ### Object containing information of devices' status ###
        # When used, should guard with status_lock
        self.status = Status(dev_list, virtual_dev_list)
        self.status_lock = threading.Lock()
        # When used should guard with rule_lock and status_lock
        # rule_scheduled stores rules scheduled to be triggered at a certain time
        # it is to handle rules with format "if xxx has been true for x time, then..."
        # If rule has changed, we clear this dictionary
        # format: {rule id: scheduled time}
        self.rule_scheduled = dict()
        # mark virtual devices' action as "automated"
        # for example, self.virtual_dev_auto_mark[dev] = (True [[val]], time) means 
        # that the virtual device "dev" has been automatically turned "True" at time
        # this is part of the status and also should be guarded with the status_lock
        self.virtual_dev_auto_mark = dict()

        ### The token to access a location from our website ###
        ###     The code for the user from our website      ###
        self.loc_token = None
        self.user_code = user_code

        ### Backend API links ###
        self.server_url = server_url
        self.rule_url = "http://" + self.server_url + "/backend/homeio/rules/"
        self.cookie_url = "http://" + self.server_url + "/backend/user/get_cookie/"
        self.trace_url = "http://" + self.server_url + "/backend/homeio/upload_trace/"
        self.monitored_dev_url = "http://" + self.server_url + "/backend/homeio/get_monitored_devs/"
        self.rule_dev_url = "http://" + self.server_url + "/backend/homeio/get_rules_and_devs/"
        self.update_monitor_url = "http://" + self.server_url + "/backend/homeio/update_monitored_devs/"
        
        self.trace = []

        self.get_funcs = {
            'Bit': self.memory_map.Instance.GetBit,
            'Byte': self.memory_map.Instance.GetByte,
            'Short': self.memory_map.Instance.GetShort,
            'Int': self.memory_map.Instance.GetInt,
            'Long': self.memory_map.Instance.GetLong,
            'Float': self.memory_map.Instance.GetFloat,
            'Double': self.memory_map.Instance.GetDouble,
            'String': self.memory_map.Instance.GetString,
            'DateTime': self.memory_map.Instance.GetDateTime,
            'TimeSpan': self.memory_map.Instance.GetTimeSpan
        }

        self.mem_types = {
            'Input': self.memory_type.Input,
            'Output': self.memory_type.Output,
            'Memory': self.memory_type.Memory
        }

        self.datetime_addr = 65

        self.exit_flag = False
        self.dry_run_rounds = 10

        # the batch size for uploading
        self.upload_batchsize = 500

        # loggers
        level = logging.INFO
        formatter = logging.Formatter('%(name)s - %(message)s')
        logger_handler = logging.StreamHandler()
        logger_handler.setFormatter(formatter)

        self.logger_rule = logging.getLogger('RULE')
        self.logger_rule.addHandler(logger_handler)
        self.logger_rule.setLevel(level)

        self.logger_monitor = logging.getLogger('MONITOR')
        self.logger_monitor.addHandler(logger_handler)
        self.logger_monitor.setLevel(level)

        self.logger_trace = logging.getLogger('TRACE')
        self.logger_trace.addHandler(logger_handler)
        self.logger_trace.setLevel(level)
