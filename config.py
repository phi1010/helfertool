#!/usr/bin/python


from os.path import split, join, dirname
import datetime


admin_email = "foo@example.com"

## das was im html <title> angezeigt wird
pagetitle = 'Helferorganisation KIF 41,5'

# Make sure all the following paths exist! (They do if you don't change
# the defaults)
basedir = dirname(__file__)
templates = join(basedir, "templates")
staticdir = join(basedir, "static")
sessionstoredir = join(basedir, "sessions")

dbfilename = join(basedir, "db", "schicht.sqlite3")

session_timeout_seconds = 1800
session_refresh_seconds = 600
session_strftime_format = '%Y-%m-%d %X.%f'

start_date = datetime.date(2013,10,29) #this is the first day which can have shifts!
conf_start_date = datetime.date(2013,10,30)
user_shift_unclaim_timeout_hours = 48

day_name = { \
		0:	'Dienstag', \
		1:	'Mittwoch', \
		2:	'Donnerstag', \
		3:	'Freitag', \
		4:	'Samstag', \
		5:	'Sonntag', \
		6:	'Montag' \
		}

shirt_stuff_changeable = True
