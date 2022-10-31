import requests
import datetime
from meta import MetaInfo
from device import Device


###################################################
# upload the traces onto the server
# called upon exit
###################################################
def generate_trace_entry(dev: Device, val, timestamp: datetime.datetime, is_automated=False):
    entry = {
        'dev_datatype': dev.datatype,
        'dev_typ': dev.typ,
        'dev_address': dev.address,
        'dev_name': dev.name,
        'val': val,
        'timestamp': timestamp.strftime('%H:%M:%S %m/%d/%Y'),
        'is_automated': is_automated
    }
    return entry
