#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime

from web.utils import render_template, expose, url_for, run_command_output, invalid_form_error
from web.session_utils import is_user_logged_in, create_session
from web.login_utils import check_login_credentials, require_login
from werkzeug import redirect

import db
import config

from Crypto.Random import random

@expose('/')
def index(request):
	return render_template('index.xml', session=request.session)


@expose('/login')
def login(request):
	if request.method != 'POST':
		return redirect('/')

	username = request.form.get('username')
	password = request.form.get('password')
	redirect_target = request.form.get('redirect_target')
	
	if not db.sane_str((username, password), True):
		msg = """Login nicht erfolgreich! Versuch es nochmal!"""
		return render_template("login.xml", message = msg, action = "/login", session=request.session)

	userid, is_admin = check_login_credentials(username, password)
	if not userid:
		msg = """Login nicht erfolgreich! Versuch es nochmal!"""
		return render_template("login.xml", message = msg, action = "/login", session=request.session)

	create_session(request.session, userid, username, is_admin)

	if not redirect_target:
		redirect_target = '/'
	return redirect(redirect_target)


@expose('/logout')
def logout(request):
	if not is_user_logged_in(request.session):
		return redirect('/')

	db.update('UPDATE person SET logged_in_since="", auth_token="" WHERE id=?', \
					(request.session['userid'],))

	request.session["username"] = None
	request.session["userid"] = None
	request.session["auth_token"] = None
	request.session['logout'] = True

	return redirect('/')

@require_login
@expose('/redirect/my_page')
def my_page(request):
	userid = request.session.get('userid')
	return redirect('/helfer/' + str(userid))


@expose('/redirect')
def redirector(request):
	if request.form.get('helfer_id'):
		return redirect('/helfer/' + request.form.get('helfer_id'))
	elif request.form.get('schicht_id'):
		return redirect('/schicht/' + request.form.get('schicht_id'))
	elif request.form.get('station_id'):
		return redirect('/station/' + request.form.get('station_id'))
	else:
		return redirect('/')


