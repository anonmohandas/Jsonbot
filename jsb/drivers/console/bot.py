# jsb/console/bot.py
#
#

""" console bot. """

## jsb imports

from jsb.lib.datadir import getdatadir
from jsb.utils.generic import waitforqueue
from jsb.lib.errors import NoSuchCommand, NoInput
from jsb.lib.botbase import BotBase
from jsb.lib.exit import globalshutdown
from jsb.utils.generic import strippedtxt, waitevents
from jsb.utils.url import striphtml
from jsb.utils.exception import handle_exception
from jsb.lib.eventhandler import mainhandler
from jsb.lib.O import datefmt, YELLOW, RED, BOLD, ENDC
from event import ConsoleEvent

## basic imports

import datetime
import time
import Queue
import logging
import sys
import code
import os
import readline
import atexit
import getpass
import re
import copy

## defines

cpy = copy.deepcopy
histfilepath = os.path.expanduser(getdatadir() + os.sep + "run" + os.sep + "console-history")

## HistoryConsole class

class HistoryConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", histfile=histfilepath):
        self.fname = histfile
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try: readline.read_history_file(histfile)
            except IOError: pass

    def save_history(self, histfile=None):
        readline.write_history_file(histfile or self.fname)

## the console

console = HistoryConsole()

## ConsoleBot

class ConsoleBot(BotBase):

    ERASE_LINE = '\033[2K'
    BOLD='\033[1m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'
    COMMON = '\003[9'

    def __init__(self, cfg=None, users=None, plugs=None, botname=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        self.type = "console"

    def startshell(self, connect=True):
        """ start the console bot. """
        self.start(False)
        while not self.stopped: 
            try: 
                input = console.raw_input("%s -=- %s%s< %s" % (time.strftime(datefmt), BOLD, YELLOW, ENDC))
                if self.stopped: return
                event = ConsoleEvent()
                event.parse(self, input, console)
                event.nooutput = True
                event.nodispatch = False
                e = self.put(event)
                res = e.wait()
                if res:
                    for r in res:
                        txt = self.makeresponse(r, dot="<br>")
                        txt = self.normalize(txt)
                        self.out(e.userhost, txt, plugorigin=e.plugorigin)
                mainhandler.handle_one()
            except IOError: break
            except NoInput: continue
            except (KeyboardInterrupt, EOFError): break
            except Exception, ex: handle_exception()
        console.save_history()

    def outnocb(self, printto, txt, *args, **kwargs):
        self._raw("%s -=- %s%s>%s %s" % (time.strftime(datefmt), BOLD, RED, ENDC, txt))

    def action(self, channel, txt, event=None):
        txt = self.normalize(txt)
        self._raw(txt)
        
    def notice(self, channel, txt):
        txt = self.normalize(txt)
        self._raw(txt)

    def exit(self, *args, **kwargs):
        """ called on exit. """
        console.save_history()
        
    def normalize(self, what):
        what = strippedtxt(what, allowed="\n")
        what = what.replace("<b>", self.BLUE)
        what = what.replace("</b>", self.ENDC)
        what = what.replace("<i>", self.YELLOW)
        what = what.replace("</i>", self.ENDC)
        what = what.replace("<h2>", self.GREEN)
        what = what.replace("</h2>", self.ENDC)
        what = what.replace("<h3>", self.GREEN)
        what = what.replace("</h3>", self.ENDC)
        what = what.replace("&lt;b&gt;", self.BOLD)
        what = what.replace("&lt;/b&gt;", self.ENDC)
        what = what.replace("<br>", "\n")
        what = what.replace("<li>", "* ")
        what = what.replace("</li>", "\n")
        if what.count(self.ENDC) % 2: what = "%s%s" %  (self.ENDC, what)
        return what
