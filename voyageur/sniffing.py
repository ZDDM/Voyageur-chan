import voyageur
import telegram
import pyshark
import pyautogui
import threading
import traceback
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
		self.last_packet = None
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
		if (message not in self.queue):
			self.queue.append(message, *arg, **kwarg)

	def handle_packet(self, packet):
		assert hasattr(packet, "irc")
		self.last_packet = packet
		irc = packet.irc
		own_packet = False
		command = ""
		parameter = ""
		trailer = ""
		prefix = ""
		try:
			for field in irc._get_all_field_lines():
				if "Command parameters" in field:
					pass

				elif "Request" in field:
					prefix = "You"
					own_packet = True

				elif "Response" in field:
					own_packet = False

				elif "Trailer" in field:
					trailer = field.split("Trailer:")[1][1:-1]

				elif "Parameter" in field:
					parameter = field.split("Parameter:")[1][1:]

				elif "Command" in field:
					command = field.split("Command:")[1]

				elif "Prefix" in field:
					prefix = field.split("Prefix:")[1].split("!")[0]

				else:
					raise Exception("Unknown field.\n '%s'"%(field))
		except AttributeError:
			traceback.print_exc()

		except IndexError:
			print("EXCEPTION IndexEror.")
			print(prefix)
			print(trailer)
			print(parameter)
			print(command)
			print(prefix)
			traceback.print_exc()

		except:
			raise

		finally:
			split = trailer.split("|")

			if "uminekoonline" in parameter.lower():
				if trailer.startswith("0") and len(split) > 2: # Normal messages.
					if prefix == "You":
						self.location_filter = split[5]
					if split[5] == self.location_filter:
						if len(split) > 13:
							for i in range(12, len(split - 1)):
								split[12] = split[12] + split[i]
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

			elif len(parameter): # Private messages.
				if len(split) > 1 and split[0] == "0":
					if prefix != "You":
						self.append("(PM / %s -> You) %s" %(prefix.replace("\n", ""), split[1]))
					else:
						self.append("(PM / You -> %s) %s" %(parameter.replace("\n", ""), split[1]))

	def run(self):
		for packet in self.capturer.sniff_continuously():
			self.handle_packet(packet)
