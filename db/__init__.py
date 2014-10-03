# coding: utf-8
import sqlite3
import os

import config


### CONFIG SECTION
INIT_COMMANDS = """
	begin transaction;
	CREATE TABLE person (id INTEGER PRIMARY KEY AUTOINCREMENT, username text NOT NULL, password text NOT NULL, email text NOT NULL, mobile text NOT NULL, comment text, logged_in_since DATETIME, auth_token text, is_admin INTEGER, tshirt_size text, pullover_size text, want_participant_shirt INTEGER, signed_hygiene INTEGER DEFAULT 0, signed_fire INTEGER DEFAULT 0, UNIQUE(username) ON CONFLICT FAIL);
	CREATE TABLE station (id INTEGER PRIMARY KEY AUTOINCREMENT, name text NOT NULL, description text NOT NULL, sort INTEGER, UNIQUE(name) ON CONFLICT FAIL);
	CREATE TABLE schicht (id INTEGER PRIMARY KEY AUTOINCREMENT, name text NOT NULL, description text NOT NULL, needed_persons integer NOT NULL, station_id INTEGER REFERENCES station(id) NOT NULL, from_day INTEGER NOT NULL, from_hour INTEGER NOT NULL, until_day INTEGER NOT NULL, until_hour INTEGER NOT NULL, UNIQUE(name, station_id, from_day, from_hour) ON CONFLICT FAIL, UNIQUE(name, station_id, until_day, until_hour) ON CONFLICT FAIL);
	CREATE TABLE schicht_order (schicht_name TEXT NOT NULL, sort INTEGER NOT NULL, UNIQUE(schicht_name));
	CREATE TABLE person_schicht ( pers_id INTEGER REFERENCES person(id), schicht_id INTEGER REFERENCES schicht(id), PRIMARY KEY(pers_id, schicht_id));
	CREATE TABLE question ( id INTEGER PRIMARY KEY AUTOINCREMENT, text text NOT NULL, title text NOT NULL, asking_person INTEGER REFERENCES person(id) NOT NULL, thread_id INTEGER REFERENCES question_threads(id) NOT NULL);
	CREATE TABLE answer ( id INTEGER PRIMARY KEY AUTOINCREMENT, question INTEGER REFERENCES question(id) NOT NULL, text text NOT NULL, thread_id INTEGER REFERENCES question_threads(id) NOT NULL);
	CREATE TABLE question_threads ( id INTEGER PRIMARY KEY AUTOINCREMENT , title text NOT NULL );
	CREATE TABLE message ( id INTEGER PRIMARY KEY AUTOINCREMENT , title text NOT NULL, content text NOT NULL, receiver INTEGER REFERENCES person(id) NOT NULL, sender INTEGER REFERENCES person(id) NOT NULL, deliveryTime DATETIME not NULL, read BOOL DEFAULT 0 NOT NULL);
	commit;
	"""
#### END CONFIG SECTION

def _init_db():
	conn = _open_db()
	conn.executescript(INIT_COMMANDS)
	conn.close()

def _open_db():
	conn = sqlite3.connect(config.dbfilename, detect_types=sqlite3.PARSE_DECLTYPES)
	conn.execute('pragma foreign_keys=ON;')
	conn.execute('pragma encoding = "UTF-8";')
	conn.row_factory = sqlite3.Row
	return conn

def select(select_string, params=None):
	conn = _open_db()
	cur = conn.cursor()
	try:
		if params:
			cur.execute(select_string, params)
		else:
			cur.execute(select_string)
		ret = cur.fetchall()
		return ret
	finally:
		conn.close()

def insert(insert_string, values):
	conn = _open_db()
	cur = conn.cursor()
	try:
		cur.execute(insert_string, values)
		conn.commit()
		ret = cur.lastrowid
		return ret
	finally:
		conn.close()

def update(update_string, values):
	conn = _open_db()
	cur = conn.cursor()
	try:
		cur.execute(update_string, values)
		conn.commit()
	finally:
		conn.close()


# checks if a variable var is of type mustBeType and if condition applies
def sane_var(var, mustBeType, condition=lambda x:True):
	try:
		var = mustBeType(var)
	except Exception:
		return False

	if not hasattr(condition, '__call__'):
		raise ValueError("condition is not a function")

	return condition(var)

#checks if a variable or a typle of variables is of type str and optionally if it is not empty
def sane_str(vars, notEmpty=False):
	if not type(vars) == tuple:
		return sane_str((vars,), notEmpty)

	for var in vars:
		if notEmpty:
			if not sane_var(var, unicode, (lambda x: not len(x.strip())==0)):
				return False
		else:
			if not sane_var(var, (lambda x: unicode)):
				return False
	return True

#checks if a variable or a typle of variables is of type int
def sane_int(vars):
	if not type(vars) == tuple:
		return sane_int((vars,))

	for var in vars:
		if not sane_var(var, int):
			return False
	return True

def sane_vars(vars, types):
	if not len(vars) == len(types):
		raise ValueError("not equally many vars and types")

	for var, type in zip(vars, types):
		if not sane_var(var, type):
			return False
	return True

if not os.path.exists(config.dbfilename):
	_init_db()

