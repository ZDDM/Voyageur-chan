import voyageur
import voyageur.utils
import telegram
import traceback
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

if voyageur.utils.determineOS() == "Linux":
	from bash import bash as command
else:
	from os import system as command
	import win32ui, win32gui, win32con, win32api

class Bot(object):
	def __init__(self, config):
		self.token = config[0]
		self.username = config[1]
		self.debug = (config[-1] == "debug")
		self.bot = telegram.Bot(token=self.token)
		self.os = voyageur.utils.determineOS()

		self.running = True
		self.UOrunning = False
		self.isSending = False # Is a message getting sent?
		self.sendIRCMessages = False # Send UO's IRC packets to the user or not.
		self.minimizeUO = False # Minimize UO's window after sending messages or not.
		self.addToQueue = False # Add user messages (not commands) to the message queue.
		self.uo_id = 0
		self.capturer = voyageur.sniffing.Capturer()
		self.last_checksum = 0
		self.checksum = 0
		self.exclusion = []
		self.send_queue = []

		self.thread = threading.Thread(target=self.update)
		self.cmd_thread = threading.Thread(target=self.input)
		self.updates = self.bot.getUpdates(-1)

		while len(self.updates) < 1:
			self.updates = self.bot.getUpdates(-1)

		self.last_id = [self.updates[-1].message.message_id, self.updates[-1].message.chat_id]
		self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: VOYAGEUR-CHAN INIT> %s"%(time.strftime("%d-%m-%Y @ %H:%M:%S")))

		if self.os == "Linux":
			if command("pidof UminekoOnline.exe"):
				self.UOrunning = True
				self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online is now running.")
				self.thread.start()
				if self.debug:
					self.cmd_thread.start()
				self.capturer.run()
			else:
				self.UOrunning = False
				self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online is not running.")
				self.checkForUO()
		elif self.os == "Windows":
			try:
				self.uo_id = win32ui.FindWindow(None, "Umineko Online")
				self.UOrunning = True
				self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online is now running.")
				self.thread.start()
				if self.debug:
					self.cmd_thread.start()
				self.capturer.run()
			except win32ui.error:
				self.UOrunning = False
				self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online is not running.")
				self.checkForUO()

	def click(self):
		if self.os == "Linux":
			command("xdotool click 1")
		elif self.os == "Windows":
			command("python -c 'import pyautogui;pyautogui.click()")

	def click_pos(self, x, y):
		if self.os == "Linux":
			command("xdotool mousemove %s %s"%(x, y))
			command("xdotool click 1")
		elif self.os == "Windows":
			command('python -c "import pyautogui;pyautogui.click(%s, %s)"'%(x,y))

	def move_mouse(self, x, y):
		if self.os == "Linux":
			command("xdotool mousemove %s %s"%(x, y))
		elif self.os == "Windows":
			pyautogui.moveTo(x, y)

	def write_text(self, text):
		if self.os == "Linux":
			command('xdotool type --clearmodifiers --delay 20 "%s"' %(text))
		elif self.os == "Windows":
			pyautogui.typewrite("%s"%(text))

	def fmaximizeUO(self):
		if self.os == "Linux":
			command("wmctrl -R 'Umineko Online'")
			self.uo_id = command("xdotool getactivewindow")
			command("xdotool windowactivate %s"%(self.uo_id))
		elif self.os == "Windows":
			self.uo_id = win32ui.FindWindow(None, "Umineko Online")
			win32gui.ShowWindow(self.uo_id.GetSafeHwnd(), win32con.SW_MAXIMIZE)
			win32gui.SetForegroundWindow(self.uo_id.GetSafeHwnd())

	def fminimizeUO(self):
		if self.os == "Linux":
			command("xdotool windowminimize %s"%(self.uo_id))
		elif self.os == "Windows":
			win32gui.ShowWindow(self.uo_id.GetSafeHwnd(), win32con.SW_MINIMIZE)

	def press_enter(self):
		if self.os == "Linux":
			command("xdotool key Return")
		elif self.os == "Windows":
			pyautogui.press("enter")

	def process_x(self, x):
		if self.os == "Linux":
			sx = int(command("(xrandr --current | grep '*' | uniq | awk '{print $1}' | cut -d 'x' -f1)").value())
		if self.os == "Windows":
			sx = win32api.GetSystemMetrics(0)
		return ((x * sx) / 1920)

	def process_y(self, y):
		if self.os == "Linux":
			sy = int(command("(xrandr --current | grep '*' | uniq | awk '{print $1}' | cut -d 'x' -f2)").value())
		if self.os == "Windows":
			sy = win32api.GetSystemMetrics(1)
		return ((y * sy) / 1080)

	def sendEnter(self):
		self.fmaximizeUO()
		self.move_mouse(self.process_x(352), self.process_y(1023))
		self.click()
		self.press_enter()
		if self.minimizeUO:
			self.fminimizeUO()

	def sendMessage(self, text):
		self.isSending = True
		ntext = text
		ntext = ntext.replace("'", "\'")
		ntext = ntext.replace('"', '\'\'')
		self.fmaximizeUO()
		if self.os == "Linux":
			self.move_mouse(self.process_x(352), self.process_y(1023))
			self.click()
		elif self.os == "Windows":
			self.click_pos(self.process_x(352), self.process_y(1023))
		self.write_text(ntext)
		self.press_enter()
		if self.minimizeUO:
			self.fminimizeUO()
		if text in self.send_queue:
			self.send_queue.remove(text)
		self.isSending = False

	def screenshot(self):
		self.fmaximizeUO()
		if self.os == "Linux":
			command("import -window $(xdotool getwindowfocus -f) /tmp/screen.png & xdotool click 1")
			return "/tmp/screen.png"
		elif self.os == "Windows":
			pyautogui.screenshot("C:\\Windows\\Temp\\screen.png")
			return "C:/Windows/Temp/screen.png"

	def checkForUO(self):
		while not self.UOrunning:
			if self.os == "Linux":
				if command("pidof UminekoOnline.exe"):
					self.UOrunning = True
					self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online is now running.")
					self.thread.start()
					self.capturer.run()
				else:
					self.UOrunning = False
			elif self.os == "Windows":
				try:
					self.uo_id = win32ui.FindWindow(None, "Umineko Online")
					self.UOrunning = True
					self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online is now running.")
					self.thread.start()
					self.capturer.run()
				except win32ui.error:
					self.UOrunning = False

	def input(self):
		while self.running:
			try:
				exec(input("EXEC> "))
			except:
				traceback.print_exc()

	def update(self):
		while self.running:
			self.updates = self.bot.getUpdates(-1)

			if self.updates[-1].message["chat"]["username"] == self.username:
				if self.os == "Linux":
					if command("pidof UminekoOnline.exe"):
						self.UOrunning = True
					else:
						self.UOrunning = False
						self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online stopped running.")
						self.checkForUO()
				elif self.os == "Windows":
					if win32ui.FindWindow(None, "Umineko Online"):
						self.UOrunning = True
					else:
						self.UOrunning = False
						self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Umineko Online stopped running.")
						self.checkForUO()
				self.last_id = [self.updates[-1].message.message_id, self.updates[-1].message.chat_id]
				if self.sendIRCMessages:
					message = self.capturer.get_next_queue()
					if message:
						self.bot.sendMessage(chat_id=self.last_id[1], text=message)
				else:
					self.capturer.queue = []

				if len(self.send_queue) > 0 and not self.isSending:
					self.sendMessage(self.send_queue[0])

				if self.last_id[0] not in self.exclusion:
					self.exclusion.append(self.last_id[0])
					if len(self.updates[-1].message["entities"]) > 0:
						if self.updates[-1].message["entities"][0]["type"] == "bot_command":
							bot_command = self.updates[-1].message.text
							if bot_command == "/start":
								pass

							if bot_command == "/sendstart":
								self.addToQueue = True
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Your messages will now be sent to UO.")

							elif bot_command == "/sendstop":
								self.addToQueue = False
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Your messages will not be sent to UO.")

							elif bot_command == "/logreceivestart":
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Deprecated. Use /ircreceivestart instead.")

							elif bot_command == "/logreceivestop":
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Deprecated. Use /ircreceivestop instead.")

							elif bot_command == "/ircreceivestart":
								self.sendIRCMessages = True
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: UO's IRC messages will now be sent to you.")

							elif bot_command == "/ircreceivestop":
								self.sendIRCMessages = False
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: UO's IRC messages will not be sent to you.")

							elif bot_command == "/diceon":
								self.capturer.diceroll = True
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: UO's dice roll messages will now be sent to you.")

							elif bot_command == "/diceoff":
								self.capturer.diceroll = False
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: UO's dice roll messages will not be sent to you.")

							elif bot_command == "/pressenter":
								self.sendEnter()
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Enter keypress simulation sent to UO.")

							elif bot_command == "/screenshot":
								if self.os == "Linux":
									image_location = self.screenshot()
									self.bot.sendChatAction(chat_id=self.last_id[1], action=telegram.ChatAction.UPLOAD_PHOTO)
									self.bot.sendPhoto(chat_id=self.last_id[1], photo=urllib.request.urlopen("file://" + image_location))
								else:
									self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Screenshots are not supported on your OS.")

							elif bot_command == "/startminimize":
								self.minimizeUO = True
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: UO's window will now be minimized after sending messages.")

							elif bot_command == "/stopminimize":
								self.minimizeUO = False
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: UO's window will not be minimized after sending messages.")

							else:
								self.bot.sendMessage(chat_id=self.last_id[1], text="INFO: Unknown command '%s'"%(bot_command))

					if self.addToQueue and not self.updates[-1].message.text.startswith("/"):
						self.send_queue.append(self.updates[-1].message.text)
