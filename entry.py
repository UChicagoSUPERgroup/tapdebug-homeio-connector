import threading
import clr
import time

clr.AddReference('EngineIO')
from EngineIO import *

from monitor import monitor
# from rule_monitor import rule_monitor
# from dev_monitor import device_monitor, init_device_monitors
from backend_monitor import rule_dev_monitor, status_update_to_backend
from meta import MetaInfo
from device import Device, init_dev_list
# from traces import upload_traces


rule_list = []
dev_list, virtual_dev_list = init_dev_list()

print("Enter the TapDebug server url: ")
print("(e.g., tapdebug.cs.uchicago.edu)")
server_url = input("Server url: ")

user_code = input("Enter the user code: ")

global_meta_info = MetaInfo(
    MemoryMap, MemoryType, MemoriesChangedEventHandler, dev_list, virtual_dev_list, rule_list, user_code, server_url)

monitor_thread = threading.Thread(
    target=monitor, args=(global_meta_info,))
monitor_thread.start()

backend_monitor_thread = threading.Thread(
    target=rule_dev_monitor, args=(global_meta_info,))
backend_monitor_thread.start()

dev_update_thread = threading.Thread(
    target=status_update_to_backend, args=(global_meta_info,))
dev_update_thread.start()

while True:
    s = input("Input 'q' to exit: \n")
    if s == 'q':
        global_meta_info.exit_flag = True
        monitor_thread.join()
        backend_monitor_thread.join()
        dev_update_thread.join()
        # upload traces
        # upload_traces(global_meta_info)
        break
