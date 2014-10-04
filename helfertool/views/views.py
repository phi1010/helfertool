#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime

from ..utils.utils import  run_command_output, invalid_form_error
from ..utils.session_utils import is_user_logged_in, create_session
from ..utils.login_utils import check_login_credentials, require_login
from flask import redirect, request, render_template, session

import helfertool.db as db
import config

from helfertool import app

from Crypto.Random import random

@app.route('/')
def index():
	return render_template('index.xml')


@app.route('/login', methods=["POST"])
def login():
	if request.method != 'POST':
		return redirect('/')

	username = request.form.get('username')
	password = request.form.get('password')
	redirect_target = request.form.get('redirect_target')
	
	if not db.sane_str((username, password), True):
		msg = """Login nicht erfolgreich! Versuch es nochmal!"""
		return render_template("login.xml", message = msg, action = "/login", session=session)

	userid, is_admin = check_login_credentials(username, password)
	if not userid:
		msg = """Login nicht erfolgreich! Versuch es nochmal!"""
		return render_template("login.xml", message = msg, action = "/login", session=session)

	create_session(session, userid, username, is_admin)

	if not redirect_target:
		redirect_target = '/'
	return redirect(redirect_target)


@app.route('/logout')
def logout():
	if not is_user_logged_in(session):
		return redirect('/')

	db.update('UPDATE person SET logged_in_since="", auth_token="" WHERE id=?', \
					(session['userid'],))

	del session["username"]
	del session["userid"]
	del session["auth_token"]
	session['logout'] = True

	return redirect('/')

@require_login
@app.route('/redirect/my_page')
def my_page():
	userid = session.get('userid')
	return redirect('/helfer/' + str(userid))


@app.route('/redirect')
def redirector():
	if request.form.get('helfer_id'):
		return redirect('/helfer/' + request.form.get('helfer_id'))
	elif request.form.get('schicht_id'):
		return redirect('/schicht/' + request.form.get('schicht_id'))
	elif request.form.get('station_id'):
		return redirect('/station/' + request.form.get('station_id'))
	else:
		return redirect('/')


