#!/usr/bin/env python3
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

'''start - Generic start. Does nothing,
sendstart - Start sending your messages to UO.
sendstop - Stop sending your messages to UO.
ircreceivestart - Start receiving UO's IRC packets.
ircreceivestop - Stop receiving UO's IRC packets.
diceon - Activate dice messages.
diceoff - Disable dice messages.
pressenter - Send enter key simulation to UO.
screenshot - Receive a screenshot of UO's window.
startminimize - Minimize UO's window after sending messages.
stopminimize - Don't minimize UO's window after sending messages.
ooc - Send messages to OOC.
stop - Generic stop. Does nothing.'''

__author__ = "Zumo"
__version__ = "0.3"
__credits__ = ["Dartz and LTexLT for creating UO. Thanks for everything!",
               "Used module's authors and contributors. Good job!",
               "Valander for suggesting the name. You're the best!"]

if __name__ == "__main__":
    print("Voyageur init.")
    voyageur.config.firstTimeRun()
    config = voyageur.config.loadConfig()
    bot = voyageur.bot.Bot(config)
else:
    raise Exception("Not running directly.")
