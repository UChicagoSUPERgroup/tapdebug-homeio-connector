Home I/O Connector for the TapDebug Web Application
===

This Python application runs a local connector between a Home I/O simulator (local) 
and the TapDebug Web Application (server-side). 

## Pre-requisites
Home I/O can be downloaded at [Home I/O](https://realgames.co/home-io/).

Please be advised that a 32-bit Python is required to run this connector software because 
Home I/O is a 32-bit application. Please check 
[Home I/O](https://docs.realgames.co/homeio/en/python/) for more details.
Since Home I/O is a Windows application, this connector also needs to run on 
Windows. The developers have checked the software with Python 3.8.10 (32-bit) 
on Windows.

Please install pythonnet.
```console
~$ python -m pip install pythonnet
```

## Running the software
Before running this software. Make sure that:
 - The TapDebug web application ([TapDebug](https://github.com/UChicagoSUPERgroup/tapdebug)) is running on a server publically accessible at \<server-url\> (e.g., tapdebug.cs.uchicago.edu).
 - A user with a \<user-code\> (e.g., user1) is created on the server.
 - A task page for the user at \<server-url\>/\<user-code\>/survey/\<task-id\> is accessed on a browser to set up the user's initial TAP rules for the task. 
 - Home I/O is running on the same machine.

Then, start the software:
```console
~$ python entry.py
```

Enter your \<server-url\> and \<user-code\> as prompted on the screen.

The TAP rules in the user's profile will control the devices in Home I/O. When clicking "Upload Trace" in the web application, the connector will also send traces since its execution to the server.