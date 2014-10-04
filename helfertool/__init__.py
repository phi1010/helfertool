from flask import Flask, render_template, session

import config

app = Flask(__name__)

import views

def removeMessages(session):
	session["messages"] = []

def is_user_admin(session):
	return is_user_logged_in(session) and session['is_admin']

def is_user_logged_in(session):
	return 'userid' in session

@app.context_processor
def additional_context():
	return {
		'helfertool_config': config,
		'is_user_logged_in': is_user_logged_in,
		'is_user_admin': is_user_admin,
		'messages_displayed': removeMessages,
		'int': int,
		'sorted': sorted,
		'unicode': unicode
	}