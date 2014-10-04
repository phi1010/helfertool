# -*- coding: utf-8 -*-

import datetime
import helfertool.db as db

def _getUserIdFromName(name):
	userid = db.select("""SELECT id
			FROM person
			WHERE 
				username = ? """,
				(name, vorname, nachname))
	
	if len(userid) == 0:
		return False #raise KeyError waere besser
	else:
		return userid[0]["id"]

## sendet eine Nachricht an den nutzer mit der Kennung to
 # to kann die nutzerid oder der username sein
def send_message(to, title, message, sender=None, deliveryTime=datetime.datetime.now()):
	
	if not type(to) == int:
		to = _getUserIdFromName(to)
		if to  == False:
			return False
	
	if not type(sender) == int and not sender == None:
		sender = _getUserIdFromName(sender)
		if sender == False:
			return False
	
	db.insert("INSERT INTO message (receiver, title, content, sender, deliveryTime) VALUES (?, ?, ?, ?, ?)",
			(to, title, message, sender, deliveryTime))
	
	return True

def display_error_message(message, session):
	if not "messages" in session.keys():
		session["messages"] = []
	
	session["messages"].append({"type":"error", "text":message})

def display_notification_message(message, session):
	if not "messages" in session.keys():
		session["messages"] = []
	
	session["messages"].append({"type":"notification", "text":message})
