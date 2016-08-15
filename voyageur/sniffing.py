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
		self.last_message = ""
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
			if next_item != self.last_message:
				self.last_message = next_item
				return next_item
			else:
				return
		else:
			return

	def append(self, message, *arg, **kwarg):
		if message not in self.queue:
			self.queue.append(message, *arg, **kwarg)

	def handle_packet(self, packet):
		assert hasattr(packet, "irc")
		irc = packet.irc
		command = ""
		parameter = ""
		trailer = ""
		prefix = ""
		own_packet = False
		try:
			if hasattr(irc, "request"):
				if not str(irc.request_command).startswith("PONG"):
					own_packet = True
					command = str(irc.request_command)
					parameter = str(irc.request_command_parameter)
					trailer = str(irc.request_trailer)
					prefix = "You"
				else:
					command = ""
					trailer = ""
					prefix = ""
			elif hasattr(irc, "response"):
				if not str(irc.response_command).startswith("PING"):
					command = str(irc.response_command)
					parameter = str(irc.response_command_parameter)
					trailer = str(irc.response_trailer)
					try:
						prefix = str(irc.response_prefix).split("!")[0]
					except:
						prefix = str(irc.response_prefix)
				else:
					command = ""
					parameter = ""
					trailer = ""
					prefix = ""
			else:
				command = ""
				parameter = ""
				trailer = ""
				prefix = ""
		except AttributeError:
			pass
		finally:
			split = trailer.split("|")

			if parameter == "##UminekoOnline":
				if trailer.startswith("0") and len(split) > 2: # Normal messages.
					if prefix == "You":
						self.location_filter = split[5]
					if split[5] == self.location_filter:
						if split[7] == "1" and split[8] != "None":
							sfxmessage = "%s played an SFX: %s"%(prefix, split[8])
							if split[9] == "0":
								self.append(sfxmessage)
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
						self.append(message)
						if split[9] == "1" and split[8] != "None":
							self.append(sfxmessage)

				elif trailer.startswith("1"): # OOC.
					message = "(OOC) %s: %s"%(prefix, split[1])
					self.append(message)

				elif trailer.startswith("2"): # Music change.
					message = "%s changed the music to %s"%(prefix, split[1])
					self.append(message)

				elif trailer.startswith("Die"): # Dice
					message = prefix + split[1]
					if self.diceroll:
						self.append(message)

				elif trailer.startswith("Location"): # Location change.
					if own_packet:
						self.location_filter = split[1]
						self.append("%s has moved to %s"%(prefix, split[1]))

					else:
						self.append("%s has moved to %s"%(prefix, split[1]))

				else:
					pass

			elif not parameter.startswith("##"): # Private messages.
				if len(split) > 1 and split[0] == "0":
					if prefix != "You":
						self.append("(PM / %s -> You) %s" %(prefix, split[1]))
					else:
						self.append("(PM / You -> %s) %s" %(parameter, split[1]))

	def run(self):
		for packet in self.capturer.sniff_continuously():
			self.handle_packet(packet)
