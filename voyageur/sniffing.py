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

class Capturer(object):
    def __init__(self, location_filter="mainbuilding"):
        self.queue = []
        self.running = True
        self.diceroll = True
        self.location_filter = location_filter
        if voyageur.utils.determineOS() == "Linux":
            self.capturer = pyshark.LiveCapture(interface="enp2s0", display_filter="irc")
        else:
            self.capturer = pyshark.LiveCapture(display_filter="irc")

    def get_next_queue(self):
        if len(self.queue) > 0:
            next_item = self.queue[0]
            del self.queue[0]
            return next_item
        else:
            return

    def handle_packet(self, packet):
        assert hasattr(packet, "irc")
        irc = packet.irc
        command = ""
        trailer = ""
        prefix = ""
        own_packet = False
        try:
            if hasattr(irc, "request"):
                if not str(irc.request_command).startswith("PONG"):
                    own_packet = True
                    command = str(irc.request_command)
                    trailer = str(irc.request_trailer)
                    prefix = "You"
                else:
                    command = ""
                    trailer = ""
                    prefix = ""
            elif hasattr(irc, "response"):
                if not str(irc.response_command).startswith("PING"):
                    command = str(irc.response_command)
                    trailer = str(irc.response_trailer)
                    try:
                        prefix = str(irc.response_prefix).split("!")[0]
                    except:
                        prefix = str(irc.response_prefix)
                else:
                    command = ""
                    trailer = ""
                    prefix = ""
            else:
                command = ""
                trailer = ""
                prefix = ""
        except AttributeError:
            pass
        finally:
            split = trailer.split("|")

            if trailer.startswith("0") and len(split) > 2: # Normal messages.
                if prefix == "You":
                    self.location_filter = split[5]
                if split[5] == self.location_filter:
                    if split[7] == "1" and split[8] != "None":
                        sfxmessage = "%s played an SFX: %s"%(prefix, split[8])
                        if split[9] == "0":
                            self.queue.append(sfxmessage)
                    if split[11] == "0":
                        message = "%s(%s)[%s]: %s"%(prefix, split[1], split[2], split[12])
                    if split[11] == "1":
                        message = "%s(%s)[%s]: <Blue> %s </blue>"%(prefix, split[1], split[2], split[12])
                    if split[11] == "2":
                        message = "%s(%s)[%s]: <Red> %s </red>"%(prefix, split[1], split[2], split[12])
                    if split[11] == "3":
                        message = "%s(%s)[%s]: <Gold> %s </gold>"%(prefix, split[1], split[2], split[12])
                    if split[11] == "4":
                        message = "%s(%s)[%s]: <Purple> %s </purple>"%(prefix, split[1], split[2], split[12])
                    self.queue.append(message)
                    if split[9] == "1" and split[8] != "None":
                        self.queue.append(sfxmessage)

            elif trailer.startswith("0") and len(split) <= 2: # Private messages.
                if prefix != "You":
                    self.queue.append("(PM / %s -> You) %s" %(prefix, split[1]))
                else:
                    self.queue.append("(PM / You -> ????) %s" %(split[1]))

            elif trailer.startswith("1"): # OOC.
                message = "(OOC) %s: %s"%(prefix, split[1])
                self.queue.append(message)

            elif trailer.startswith("2"): # Music change.
                message = "%s changed the music to %s"%(prefix, split[1])
                self.queue.append(message)

            elif trailer.startswith("Die"): # Dice
                message = prefix + split[1]
                if self.diceroll:
                    self.queue.append(message)

            elif trailer.startswith("Location"): # Location change.
                if own_packet:
                    self.location_filter = split[1]
                    self.queue.append("%s has moved to %s"%(prefix, split[1]))

                else:
                    self.queue.append("%s has moved to %s"%(prefix, split[1]))

            else:
                pass

    def run(self):
        for packet in self.capturer.sniff_continuously():
            self.handle_packet(packet)
