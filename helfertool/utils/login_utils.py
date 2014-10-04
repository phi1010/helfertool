# -*- coding: utf-8 -*-

from session_utils import is_user_logged_in, is_user_admin
import helfertool.db as db

from flask import render_template, session

from passlib.hash import sha256_crypt


# returns tuple (userid, uid_was_found)
def _find_userid_byname(username):
	rows = db.select('SELECT id FROM person WHERE username=?', (username,))
	if len(rows) != 1:
		return None, False

	return rows[0]['id'], True


# returns tuple (userid, uid_was_found)
def _find_username_byid(userid):
	rows = db.select('SELECT username FROM person WHERE id=?', (userid,))
	if len(rows) != 1:
		return None, False

	return rows[0]['username'], True


def check_login_credentials(username, password):
	## ja, das (username,) muss so, damit das ganze ein tupel wird und nicht
	## eine grouped sequence (da würden die einzelnen chars in die luecken fürs
	## sql eingesetzt werden
	rows = db.select("SELECT * FROM person WHERE username=?", (username,))

	## row['password'] is the crypted password with salt prepended
	if rows == [] or not sha256_crypt.verify(password, rows[0]['password']):
		return False, False

	if rows[0]['is_admin'] == 1:
		is_admin = True
	else:
		is_admin = False

	return rows[0]['id'], is_admin ## no other way to get user-id otherwise..

def require_login(function):
	def decorator2(*args, **name):
		request = args[0]

		if is_user_logged_in(session):
			return function(*args, **name) 
		else:
			return render_template("login.xml",
					message = "Bitte log dich ein, um diese Funktion zu nutzen.",
					redirect_target = request.url, session=session)

	return decorator2


## it is very important to use this decorator only where you made sure that the
## user is logged in. typically you'd achieve this by first requiring to log in:
##
## @require_login
## @require_admin
## def foo(request):
##     bar
def require_admin(func):
	def require_admin_decorator(*args, **name):
		request = args[0]

		if not is_user_admin(session):
			return render_template('error.xml',
					error_short='requires admin rights',
					error_long='''the action you were trying to perform requires
					admin priviliges, which you dont have''',
					session=session)

		return func(*args, **name)

	return require_admin_decorator
