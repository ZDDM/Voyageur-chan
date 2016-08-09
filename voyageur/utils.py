import voyageur
import telegram
import pyshark
import pyautogui
import threading
import socket
import hashlib
import urllib
import logging
import time
import sys
import os

def determineOS(): # Determines which OS is the user running currently.
    if sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform.startswith("win32"):
        return "Windows"
    else:
        raise Exception("Operative system \"%s\" not supported"%(os.platform))
        sys.exit(1)
