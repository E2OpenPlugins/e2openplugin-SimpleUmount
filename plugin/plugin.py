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
# VERSION : 0.04  2011-11-12

PLUGIN_VERSION = "0.04"

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


# --- Main plugin code

class SimpleUmount(Screen):
	global PLUGIN_VERSION
	# plugin main screen (coord X,Y where 0,0 is upper left corner)
	skin = """
		<screen position="center,center" size="680,400" title="SimpleUmount rel. """ + PLUGIN_VERSION + """">
			<widget name="wdg_label_instruction" position="10,10" size="660,30" font="Regular;20" />
			<widget name="wdg_label_legend_1" position="10,60" size="130,30" font="Regular;20" />
			<widget name="wdg_label_legend_2" position="140,60" size="150,30" font="Regular;20" />
			<widget name="wdg_label_legend_3" position="320,60" size="150,30" font="Regular;20" />
			<widget name="wdg_label_legend_4" position="500,60" size="150,30" font="Regular;20" />
			<widget name="wdg_menulist_device" position="10,90" size="660,300" font="Fixed;20" />
		</screen>
		"""

	def __init__(self, session):

		print "[SimpleUmount] ++ START PLUGIN ++"
		Screen.__init__(self, session)
		self.session = session

		# set buttons
		self["actions"] = ActionMap( ["OkCancelActions", "DirectionActions"],
						{
						"cancel": self.Exit,
						"ok": self.Umount,
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


	def Exit(self):
		print "[SimpleUmount] exit"
		self.close()


	def umountConfirm(self, result):
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


	def Umount(self):
		if self.noDeviceError == False :
			selected = self["wdg_menulist_device"].getSelectedIndex()
			self.session.openWithCallback(self.umountConfirm, MessageBox, text = _("Really umount device") + " " + self.list_dev[selected] + " ?", type = MessageBox.TYPE_YESNO, timeout = 10, default = False )


	def getDevicesList(self):
		self.wdg_list_dev = []
		self.list_dev = []
		r = os.popen('mount | grep "/dev/sd" | sort', 'r')
		lines = r.readlines()

		if len(lines) == 0:
			self.wdg_list_dev.append( _("WARNING: cannot read any mount point") )
			self.wdg_list_dev.append( _("probably no mass storage device inserted") )
			self.noDeviceError = True
		else:
			for line in (lines):
				l = re.split('\s+',line)
				r2 = os.popen('df ' + l[0])
				lines2 = r2.readlines()
				if len(lines2) > 1:
					l2 = re.split('\s+',lines2[1])
					size = int(l2[1])/1024
				else:
					size = "????"
				r2.close()
				self.list_dev.append(l[0])
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


