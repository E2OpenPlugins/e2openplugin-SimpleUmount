# -*- coding: utf-8 -*-

#
#                             <<< SimpleUmount >>>
#                         
#                                                                            
#  This file is open source software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License version 2 as
#               published by the Free Software Foundation.
#                                                                            
#
# Simple Enigma2 plugin extension to show list of mounted mass storage devices 
# and umount one of them with a simple [OK] click on remote.
#
# Useful if you insert a USB HDD or USB FLASH DRIVE and, before remove it,
# you MUST umount it to avoid filesystem damage
#
# AUTHOR: ambrosa  (thanks to Skaman for suggestions)
# EMAIL: aleambro@gmail.com
# VERSION : 0.05  2011-11-13

PLUGIN_VERSION = "0.05"

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label
from Components.MenuList import MenuList

import os
import re


# --- Internationalization
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "SimpleUmount"
PluginLanguagePath = "Extensions/" + PluginLanguageDomain + "/po"

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))
	gettext.bindtextdomain('enigma2', resolveFilename(SCOPE_LANGUAGE, ""))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		# fallback to default translation for txt
		t = gettext.dgettext("enigma2",txt)
	return t

localeInit()
# -----------------------------------------------------------------

# --- Init config
from Components.config import KEY_LEFT, KEY_RIGHT, config, ConfigYesNo, NoSave, ConfigSelection, getConfigListEntry, ConfigSubsection, ConfigText
from Components.ConfigList import ConfigList, ConfigListScreen

config.plugins.simpleumount = ConfigSubsection()
config.plugins.simpleumount.showonlyremovable = ConfigYesNo(default = True)
# -----------------------------------------------------------------

# --- Main plugin code

class SimpleUmount(Screen):
	global PLUGIN_VERSION
	# plugin main screen (coord X,Y where 0,0 is upper left corner)
	skin = """
		<screen position="center,center" size="680,450" title="SimpleUmount rel. """ + PLUGIN_VERSION + """">
			<widget name="wdg_label_instruction" position="10,10" size="660,30" font="Regular;20" />
			<widget name="wdg_label_legend_1" position="10,60" size="130,30" font="Regular;20" />
			<widget name="wdg_label_legend_2" position="140,60" size="150,30" font="Regular;20" />
			<widget name="wdg_label_legend_3" position="320,60" size="150,30" font="Regular;20" />
			<widget name="wdg_label_legend_4" position="500,60" size="150,30" font="Regular;20" />
			<widget name="wdg_menulist_device" position="10,90" size="660,300" font="Fixed;20" />
			<widget name="wdg_config" position="10,410" size="660,30" font="Regular;20" />
		</screen>
		"""

	def __init__(self, session):

		print "[SimpleUmount] ++ START PLUGIN ++"
		Screen.__init__(self, session)
		self.session = session

		# set buttons
		self["actions"] = ActionMap( ["OkCancelActions", "DirectionActions"],
						{
						"cancel": self.exitPlugin,
						"ok": self.umountDevice,
						"left": self.keyLeft,
						"right": self.keyRight
						},
					 -1 )

		self["wdg_label_instruction"] = Label( _("Select device and press OK to umount or EXIT to quit") )
		self["wdg_label_legend_1"] = Label( _("DEVICE") )
		self["wdg_label_legend_2"] = Label( _("MOUNTED ON") )
		self["wdg_label_legend_3"] = Label( _("TYPE") )
		self["wdg_label_legend_4"] = Label( _("SIZE") )

		self.wdg_list_dev = []
		self.list_dev = []
		self.noDeviceError = True
		self["wdg_menulist_device"] = MenuList( self.wdg_list_dev )
		self.getDevicesList()

		# I use configList (more complex approach) to be ready in future to add other config options
		self.configList = []
		self["wdg_config"] = ConfigList(self.configList, session = self.session)
		self.configList.append( ( _("Show only removable devices"), config.plugins.simpleumount.showonlyremovable) )
		self["wdg_config"].setList(self.configList)


	def keyLeft(self):
			self["wdg_config"].handleKey(KEY_LEFT)
			for x in self["wdg_config"].list:
				x[1].save()
			self.getDevicesList()


	def keyRight(self):
			self["wdg_config"].handleKey(KEY_RIGHT)
			for x in self["wdg_config"].list:
				x[1].save()
			self.getDevicesList()


	def exitPlugin(self):
		self.close()


	def umountDeviceConfirm(self, result):
		if result :
			selected = self["wdg_menulist_device"].getSelectedIndex()
			r = os.popen('umount -f %s 2>&1' % (self.list_dev[selected]), 'r' )
			lines = r.readlines()
			retcode = r.close()
			if retcode != None:
				errmsg = '\n\n' + _("umount return code") + ": %s" % (retcode)
				for line in lines:
					errmsg = errmsg + "\n" + line
				self.session.open(MessageBox, text = _("Cannot umount device") + " " + self.list_dev[selected] + errmsg, type = MessageBox.TYPE_ERROR, timeout = 10)

		self.getDevicesList()


	def umountDevice(self):
		if self.noDeviceError == False :
			selected = self["wdg_menulist_device"].getSelectedIndex()
			self.session.openWithCallback(self.umountDeviceConfirm, MessageBox, text = _("Really umount device") + " " + self.list_dev[selected] + " ?", type = MessageBox.TYPE_YESNO, timeout = 10, default = False )


	def getDevicesList(self):
		global config

		self.wdg_list_dev = []
		self.list_dev = []

		# extract sd* mounted devices
		r = os.popen('mount | grep "/dev/sd" | sort', 'r')
		# expected output example:
		#    /dev/sda6 on / type ext4 (rw,errors=remount-ro,commit=0)
		#    /dev/sda7 on /home type ext4 (rw,commit=0)

		lines = r.readlines()

		if len(lines) == 0:
			self.wdg_list_dev.append( _("WARNING: cannot read any mount point") )
			self.wdg_list_dev.append( _("probably no mass storage device inserted") )
			self.noDeviceError = True
		else:
			for line in (lines):
				l = re.split('\s+',line)

				# extract device size
				r2 = os.popen('df ' + l[0])
				# expected output example:
				#    File system         blocchi di 1K   Usati   Dispon. Uso% Montato su
				#    /dev/sda6             28835836   4740816  22630240  18% /

				lines2 = r2.readlines()
				if len(lines2) > 1:
					l2 = re.split('\s+', lines2[1])
					size = int(l2[1]) / 1024
				else:
					size = "????"
				r2.close()

				removable = 0
				removable_path = "/sys/block/" + l[0][5:8] + "/removable"
				if os.path.exists(removable_path) :
					fd = open(removable_path, 'r')
					stmp = str(fd.read())
					stmp = stmp.strip('\n\r\t ')
					fd.close()
					if stmp == '1':
						removable = 1
					print "[SimpleUmount] stmp = -%s-" % (stmp)
				print "[SimpleUmount] config = -%s-" % (config.plugins.simpleumount.showonlyremovable.value)
				print "[SimpleUmount] removable -%s- = -%s-" % (l[0][5:8], removable)

				if config.plugins.simpleumount.showonlyremovable.value == 0 or removable == 1 :
					self.list_dev.append([l[0]])
					self.wdg_list_dev.append( "%-10s %-14s %-11s %8sMB" % (l[0], l[2], l[4]+','+l[5][1:3], size) )

			self.noDeviceError = False

		r.close()
		self["wdg_menulist_device"].setList(self.wdg_list_dev)

		return

# ----------------------------------------------------------------------------------

def main(session, **kwargs):
	session.open(SimpleUmount)

def Plugins(**kwargs):
	global PLUGIN_VERSION

	plug = list()
	plug.append( PluginDescriptor(name = "SimpleUmount", 
			description = _("Simple mass storage umounter extension"), 
			where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main) )

	return plug


