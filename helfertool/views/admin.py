#!/usr/bin/python
# -*- coding: utf-8 -*-

from ..utils.utils import  run_command_output, invalid_form_error
from ..utils.session_utils import is_user_admin
from ..utils.login_utils import require_login, require_admin, _find_userid_byname

from helfertool import app

from flask import redirect, request, render_template,session

from passlib.hash import sha256_crypt

import helfertool.db as db

@require_login
@require_admin
@app.route('/admin/toggle', methods=["GET", "POST"])
def toggle_admin_flag():
	if request.method != 'POST':
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didnt send a POST request. we don\'t understand anything else',
				session=session)
	
	userid = request.form.get('toggle_uid')
	valid_uid = True
	if not db.sane_int(userid):
		valid_uid = False

	rows = db.select('SELECT * FROM person WHERE id=?', (userid,))
	if len(rows) != 1:
		valid_uid = False

	if not valid_uid:
		return render_template('error.xml',
				error_short='invalid userid',
				error_long='that is not a valid userid',
				session=session)

	## probably ok by now
	was_admin_before = rows[0]['is_admin']
	db.update('UPDATE person SET is_admin=? WHERE id=?',
			(not was_admin_before, userid))

	return redirect('/admin')


@require_login
@require_admin
@app.route('/admin/claim_schicht', methods=["POST"])
def admin_claim_schicht():
	if request.method != 'POST':
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didnt send a POST request. we don\'t understand anything else',
				session=session)

	## XXX is it ok to use username here? should be, because the login checker
	## corrects it if anyone tried to fiddle with it
	username = request.form.get('username')
	schicht_id = request.form.get('schicht_id')

	if not db.sane_int(schicht_id) or not db.sane_str(username):
		return invalid_form_error(session, msg=u"schicht_id keine zahl oder username kein string")

	userid, found = _find_userid_byname(username)
	if not found:
		return invalid_form_error(session, msg=u"user existiert nicht.  sicher dass du dich angemeldet hast?")

	db.insert('INSERT INTO person_schicht (pers_id, schicht_id) VALUES (?, ?)', (userid, schicht_id))

	redirect_target = request.form.get('redirect_target')
	if not redirect_target:
		redirect_target = '/schicht'


	return redirect(redirect_target)


@require_login
@require_admin
@app.route('/admin/changepw', methods=["POST"])
def userpw_aendern():
	if request.method != 'POST':
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didnt send a POST request. we don\'t understand anything else',
				session=session)

	userid = request.form.get('userid')
	new_pass = request.form.get('new_pass')

	crypted = sha256_crypt.encrypt(new_pass)
	db.update('UPDATE person SET password=? WHERE id=?', (crypted, userid))

	return redirect('/admin')

@require_login
@require_admin
@app.route('/admin/has_signed', methods=["POST"])
def userpw_signed():
	if request.method != 'POST':
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didnt send a POST request. we don\'t understand anything else',
				session=session)

	userid = request.form.get('userid')
	signed_hygiene = 1 if request.form.get('signed_hygiene') else 0
	signed_fire = 1 if request.form.get('signed_fire') else 0

	db.update('''UPDATE person
	SET
		signed_hygiene=?, signed_fire=?
	WHERE id=?''', (signed_hygiene, signed_fire, userid))

	return redirect('/admin')



@require_login
@require_admin
@app.route('/admin/user_unclaim_schicht')
def user_unclaim_schicht():
	if request.method != 'GET':
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didnt send a GET request. we don\'t understand anything else',
				session=session)

	if not 'userid' in request.args or not 'schichtid' in request.args or not 'tag' in request.args:
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didnt send userid or schichtid parameters. we cannot work like this',
				session=session)

	userid = request.args['userid']
	schichtid = request.args['schichtid']
	tag = request.args['tag']

	if not db.sane_int((userid, schichtid, tag)):
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you didn\'t provide numeric arguments. we cannot work like that',
				session=session)
	
	userid = int(userid)
	schichtid = int(schichtid)
	tag = int(tag)

	db.update('DELETE FROM person_schicht WHERE pers_id=? AND schicht_id=?',
			(request.args['userid'], request.args['schichtid']))

	## redirect zu da wo der request typischerweise her kommt
	return redirect('/schicht#tabs-%d' % tag)


@require_login
@require_admin
@app.route('/admin')
def admin_view():
	if request.method == 'GET':
		users = db.select('SELECT * FROM person')

		schichten = {}
		for u in users:
			schichten[u['username']] = db.select('''SELECT
						? AS userid,
						p.mobile  AS mobile,
						p.email AS email,
						p.signed_hygiene as signed_hygiene,
						p.signed_fire as signed_fire,
						COUNT(ps.schicht_id) AS schicht_count,
						p.tshirt_size as tshirt,
						p.pullover_size as zipper
				FROM
						person AS p
				LEFT OUTER JOIN
						person_schicht AS ps ON p.id = ps.pers_id
				WHERE
						p.id = ?''',
					(u['id'],u['id']))[0] ## that query returns a one-element
					               ## list for everything

		conflicts = db.select('''SELECT
					ps.pers_id as pid, group_concat(DISTINCT s.id) as sids
				FROM
					schicht as s
				JOIN person_schicht as ps ON
					s.id = ps.schicht_id
				JOIN person_schicht as ps2 ON
					ps.pers_id = ps2.pers_id
				JOIN schicht as s2 ON
					s2.id = ps2.schicht_id AND s.id != s2.id
				WHERE
					((s.from_day * 24 + s.from_hour <= s2.from_day * 24 + s2.from_hour) AND
						(s.until_day * 24 + s.until_hour > s2.from_day * 24 + s2.from_hour)) OR
					((s.from_day * 24 + s.from_hour < s2.until_day * 24 + s2.until_hour) AND
						(s.until_day * 24 + s.until_hour >= s2.until_day * 24 + s2.until_hour)) OR
					((s.from_day * 24 + s.from_hour >= s2.from_day * 24 + s2.from_hour) AND
						(s.until_day * 24 + s.until_hour <= s2.until_day * 24 + s2.until_hour))
				GROUP BY ps.pers_id;''')

		howmany = db.select('''SELECT
					sum(s.needed_persons) AS want,
					(SELECT
						count(ps.schicht_id)
					FROM
						person_schicht AS ps) AS have
				FROM schicht AS s;''')

		return render_template('admin.xml', session=session,
				users=users, schichten=schichten, conflicts=conflicts, howmany=howmany[0])

	else:
		return render_template('error.xml',
				error_short='invalid request',
				error_long='you sent neither a POST nor a GET request. we don\'t understand anything else',
				session=session)

