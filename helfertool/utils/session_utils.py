#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date

import helfertool.db as db
import config
import hashlib

from Crypto.Random import random

## only call this after the user did authenticate
def create_session(session, userid, username, is_admin):
	## generate auth token
	auth_token = hashlib.md5("".join([ random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for i in range(0, 12)])).hexdigest()

	## update db entry
	db.update('UPDATE person SET auth_token=?, logged_in_since=? WHERE id=?', \
			(auth_token, datetime.now(), userid))
	session["auth_token"] = auth_token
	session['userid'] = userid
	session['username'] = username
	session['is_admin'] = is_admin

	if not validate_session(session):
		assert False


def is_user_admin(session):
	return is_user_logged_in(session) and session['is_admin']

def is_user_logged_in(session):
	return 'userid' in session and not session['userid'] == None

def validate_session(session):
	if not 'userid' in session or not 'auth_token' in session or not 'username' in session or not 'is_admin' in session or \
			not session['userid'] or not session['auth_token'] or session['auth_token'] == "":
		return False

	rows = db.select('SELECT * FROM person WHERE id = ?', (session['userid'],))
	if len(rows) != 1:
		return False

	if session['auth_token'] != rows[0]['auth_token'] or session['username'] != rows[0]['username']:
		return False

	if session['is_admin'] and rows[0]['is_admin'] != 1 or \
			not session['is_admin'] and rows[0]['is_admin'] == 1:
		return False

	if not rows[0]['logged_in_since'] or rows[0]['logged_in_since'] == None:
		return False

	now = datetime.now()
	then = datetime.strptime(rows[0]['logged_in_since'], \
			config.session_strftime_format)

	if (now - then).total_seconds() >= config.session_timeout_seconds:
		return False

	## at this point we're sufficiently sure that the user and session are valid

	## update last active timestamp in db if we haven't recently
	if (now - then).total_seconds() > config.session_refresh_seconds:
		db.update('UPDATE person SET logged_in_since=? WHERE id=?', (now,session['userid']))

	days = (config.conf_start_date - date.today()).days
	if not days in session or days != session['days']:
		session['days'] = days

	return True


