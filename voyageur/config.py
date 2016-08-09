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

global path

path = {"Windows" : "%s\\voyageur.cfg"%(os.getenv("APPDATA")),
        "Linux"   : "%s/.config/voyageur.cfg"%(os.getenv("HOME"))}

def loadConfig():
    global path
    try:
        with open(path[voyageur.utils.determineOS()], "r+") as config:
            cfg = []
            for i in config.readlines():
                cfg.append(i.replace("\n", ""))
            return cfg
    except:
        raise

def writeConfig(seq, access="w+"):
    global path
    try:
        with open(path[voyageur.utils.determineOS()], access) as config:
            config.writelines(seq)
    except:
        pass

def firstTimeRun():
    if not os.path.isfile(path[voyageur.utils.determineOS()]):
        print("-------- Welcome to Voyageur-chan! ---------")
        print("A bot for people who have lives outside UO.")
        print("-------------------------------------------")
        print()
        print("It seems like this is your first time running Voyageur-chan.")
        print("Well, either way I need you to get some info for me, okay?")
        print("What's your bot's token?")
        token = input("TOKEN> ")
        print("Okay! Now I need you to input your Telegram username without @.")
        print("Like this -> 'exampleusername'")
        username = input("USERNAME> ")
        print("Thank you!")
        print()
        print("TOKEN ->", token)
        print("USERNAME ->", username)
        print("Is this okay?")
        choice = input("Y/N> ")
        if choice.lower() in ["y", "yes", "sí", "si"]:
            writeConfig([token + "\n", username], "a")
            print("That's all you needed to config.")
            time.sleep(1)
            print("")
            return True
        elif choice.lower() in ["n", "no"]:
            print("Is it not okay...?")
            print("Well, you're unlucky.")
            print("Please restart the bot again.")
            time.sleep(5)
            sys.exit(1)
        else:
            print("Oh, so you think you're funny. Huh?")
            print("Well, you're unlucky.")
            print("Please restart the bot again.")
            time.sleep(5)
            sys.exit(1)
    else:
        return False
