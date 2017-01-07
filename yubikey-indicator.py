#!/usr/bin/env python3

"""yubikey-indicator.py: A Yubikey indicator applet for Unity"""

__author__ = "Jeff Channell"
__copyright__ = "Copyright 2017, Jeff Channell"
__credits__ = ["Jeff Channell"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Jeff Channell"
__email__ = "me@jeffchannell.com"
__status__ = "Prototype"

import gi
import signal
import os.path
import re
import subprocess
import sys
import usb.core
import usb.util

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import GLib
from subprocess import run

class YubikeyIndicator:
	def __init__(self):
		self.about = None
		self.indicators = dict()
		self.models = {
			"YubiKey": [0x0010],
			"YubiKey NEO": [0x0111],
			"Yubikey Touch U2F Security Key": [0x0120]
		}
		
		indicator = appindicator.Indicator.new_with_path(
			"YubikeyIndicatorNone",
			"icon-yubikey-none",
			appindicator.IndicatorCategory.HARDWARE,
			"{}/icons".format(os.path.dirname(os.path.realpath(__file__)))
		)
		indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		menu = Gtk.Menu()

		# add a yubikey-personalization-gui menu item
		item = Gtk.MenuItem()
		item.set_label("Open Yubikey Personalization GUI")
		item.connect("activate", self.run_yubikey_gui)
		menu.append(item)
		
		# sep
		item = Gtk.SeparatorMenuItem()
		menu.append(item)
		
		# about me
		item = Gtk.MenuItem()
		item.set_label("About")
		item.connect("activate", self.show_about)
		menu.append(item)
		
		# add a quit menu item
		item = Gtk.MenuItem()
		item.set_label("Quit")
		item.connect("activate", self.quit)
		menu.append(item)
		
		# set the menu
		menu.show_all()
		indicator.set_menu(menu)
		
		self.nokey = indicator
			
	def add_about_window_contents(self):
		text = Gtk.Label()
		text.set_markup(
			"<b>About YubikeyIndicator</b>\n\n{}\n\n"
			"A Yubikey indicator applet for Unity\n\n"
			"<a href=\"https://github.com/jeffchannell/yubikey-indicator\">"
			"https://github.com/jeffchannell/yubikey-indicator</a>\n\n"
			"<small>"
			"© 2017 Jeff Channell\n\n"
			"This program comes with absolutely no warranty.\n"
			"See the GNU General Public License, version 3 or later for details."
			"</small>".format(__version__)
		)
		text.set_line_wrap(True)
		text.set_justify(Gtk.Justification.CENTER)
		self.about.add(text)
			
	def destroy_about(self, widget, something):
		self.about = None
		return False

	def do_nothing(self, widget):
		pass
		
	def get_indicator_key(self, key, prod):
		return "{}-{}".format(key, prod)
		
	def handle_indicator(self, key, prod):
		indicatorKey = self.get_indicator_key(key, prod)
		if indicatorKey not in self.indicators.keys():
			icon = "icon-yubikey"
			if re.search('u2f', prod, re.IGNORECASE):
				icon = "icon-yubikey-u2f"
			
			indicator = appindicator.Indicator.new_with_path(
				"YubikeyIndicator{}".format(indicatorKey),
				icon,
				appindicator.IndicatorCategory.HARDWARE,
				"{}/icons".format(os.path.dirname(os.path.realpath(__file__)))
			)
			indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
			menu = Gtk.Menu()

			# add a yubikey-personalization-gui menu item
			item = Gtk.MenuItem()
			item.set_label("Open Yubikey Personalization GUI")
			item.connect("activate", self.run_yubikey_gui)
			menu.append(item)
			
			# sep
			item = Gtk.SeparatorMenuItem()
			menu.append(item)

			# yubikey model
			item = Gtk.MenuItem()
			item.set_label("Model:\t{}".format(prod))
			item.connect("activate", self.do_nothing)
			menu.append(item)
			
			# sep
			item = Gtk.SeparatorMenuItem()
			menu.append(item)
			
			# about me
			item = Gtk.MenuItem()
			item.set_label("About")
			item.connect("activate", self.show_about)
			menu.append(item)
			
			# add a quit menu item
			item = Gtk.MenuItem()
			item.set_label("Quit")
			item.connect("activate", self.quit)
			menu.append(item)
			
			# set the menu
			menu.show_all()
			indicator.set_menu(menu)
			
			self.indicators[indicatorKey] = indicator
		
	def main(self):
		self.run_loop()
		Gtk.main()

	def quit(self, widget):
		Gtk.main_quit()
		
	def remove_missing(self, found):
		missing = []
		for key in self.indicators.keys():
			if key not in found:
				missing.append(key)
		if len(missing):
			for key in missing:
				del self.indicators[key]
		
	def run_loop(self):
		keys = 0
		found = []
		yubikeys = usb.core.find(find_all=1, idVendor=0x1050)
		if yubikeys is not None:
			for yubikey in yubikeys:
				try:
					if yubikey._product is None:
						yubikey._product = usb.util.get_string(yubikey, yubikey.iProduct)
					self.handle_indicator(keys, yubikey._product)
					found.append(self.get_indicator_key(keys, yubikey._product))
					keys = keys + 1
				except Exception as e:
					for prod in self.models.keys():
						if yubikey.idProduct in self.models[prod]:
							self.handle_indicator(keys, prod)
							found.append(self.get_indicator_key(keys, prod))
							keys = keys + 1
		
		if len(found) is 0:
			self.nokey.set_status(appindicator.IndicatorStatus.ACTIVE)
		else:
			self.nokey.set_status(appindicator.IndicatorStatus.PASSIVE)
			
		self.remove_missing(found)
		# end with another loop
		GLib.timeout_add_seconds(1, self.run_loop)
		
	def run_yubikey_gui(self, widget):
		run(["yubikey-personalization-gui"])
		
	def show_about(self, widget):
		if None == self.about:
			self.about = Gtk.Window()
			self.about.set_title("About YubikeyInidicator")
			self.about.set_keep_above(True)
			self.about.connect("delete-event", self.destroy_about)
			self.add_about_window_contents()
			
		self.about.set_position(Gtk.WindowPosition.CENTER)
		self.about.set_size_request(400, 200)
		self.about.show_all()
		

def main():
	# allow app to be killed using ctrl+c
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	indicator = YubikeyIndicator()
	indicator.main()

if __name__ == '__main__':
	main()
