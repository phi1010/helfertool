# -*- coding: utf-8 -*-

from web.utils import render_template, expose, url_for, run_command_output, invalid_form_error
from web.login_utils import require_login, is_user_logged_in, require_admin, is_user_admin

from werkzeug import redirect
import db
import config

import itertools
import datetime
import math
from copy import deepcopy

## neue schicht anlegen
@require_login
@require_admin
@expose('/schicht/new')
def neue_schicht(request):
	if request.method == 'GET':
		## formular anzeigen, weil noch kein POST-foo
		stations = db.select('SELECT id, name FROM station')

		return render_template('schicht_anlegen.xml',
				session=request.session, stations=stations)

	## else: neue schicht eintragen
	name = request.form.get('name')
	station_id = request.form.get('station_id')
	desc = request.form.get('desc')
	#wird exceptions werfen, wenn nutzer bullshit schickt, aber besser hier als anderswo!
	needed_persons = request.form.get('needed_persons')
	from_day = request.form.get('from_day')
	until_day = request.form.get('until_day')
	from_hour = request.form.get('from_hour')
	until_hour = request.form.get('until_hour')

	## kann hier eh nur admin, der tut ja nix böses..
	if not db.sane_str(name, True) or not db.sane_str(desc) \
		or not db.sane_int((station_id, needed_persons, from_day, until_day, from_hour, until_hour)):
		return invalid_form_error(request.session,
				msg="name leer oder irgendwo ungültige zeichen")
	station_id = int(station_id)
	needed_persons = int(needed_persons)
	from_day = int(from_day)
	until_day = int(until_day)
	from_hour = int(from_hour)
	until_hour = int(until_hour)

	if from_day > until_day or ( from_day==until_day and from_hour >= until_hour ):
		return invalid_form_error(request.session)

	ret = db.insert("""INSERT INTO
				schicht (name, description, needed_persons, station_id, from_day, until_day, from_hour, until_hour)
			   VALUES
			   	(?, ?, ?, ?, ?, ?, ?, ?)""",
			(name, desc, needed_persons, station_id, from_day, until_day, from_hour, until_hour))

	ret = db.insert("""INSERT INTO
				schicht_order (schicht_name, sort)
			VALUES
				(?, ?)""",
			(name, 1))

	return redirect('/schicht')


## sich für diese eine schicht vormerken lassen
@require_login
@expose('/schicht/claim')
def claim_schicht(request):
	if request.method != 'POST':
		return redirect('/schicht')

	pers_id = request.session["userid"]
	schicht_id = request.form.get('schicht_id')

	if not db.sane_int(schicht_id):
		return invalid_form_error(request.session)

	db.insert('INSERT INTO person_schicht (pers_id, schicht_id) VALUES (?, ?)', (pers_id, schicht_id))

	redirect_target = request.form.get('redirect_target')
	if not redirect_target:
		redirect_target = '/schicht'

	return redirect(redirect_target)


@require_login
@expose('/schicht/unclaim')
def schicht_dochned(request):
	## fiddle out helferid
	helferid = request.form.get('helfer_id')
	schicht_id = request.form.get('schicht_id')
	if (helferid == None and schicht_id == None):
		helferid = request.args['helfer_id']
		schicht_id = request.args['schicht_id']

	## If a tag is set, we came from the schichtplan
	tag = -1
	if 'tag' in request.args:
		tag = request.args['tag']

	if not db.sane_int((helferid, schicht_id, tag)):
		return invalid_form_error(request.session, 'parameters not numeric')
	helferid = int(helferid)
	schicht_id = int(schicht_id)
	tag = int(tag)

	## check this is the user with that very id
	if not request.session["userid"] or not helferid or request.session["userid"] != helferid:
		return render_template('error.xml', error_short='unauthorized',
			error_long="du kannst nur deine eigenen schichten anschauen oder aendern. entweder du bist nicht eingeloggt, oder du versuchst schichten anderer leute anzuzeigen oder zu veraendern",
			config=config, session=request.session)

	res = db.select("SELECT from_day, from_hour FROM schicht WHERE id=?",
			(schicht_id,))
	
	if not len(res)==1:
		return render_template('error.xml', error_short='meh',
			error_long="diese schicht gibt es nicht!",
			config=config, session=request.session)
	else:
		res = res[0]
		
	daysSinceStart =  (datetime.date.today()-config.start_date).days
	curHours = datetime.datetime.time(datetime.datetime.now()).hour
	
	if res["from_day"]*24 + res["from_hour"] < daysSinceStart*24 + curHours + config.user_shift_unclaim_timeout_hours + 1: # +1 wg angefangene Stunden abziehen
		return render_template('error.xml', error_short=u'Zu spät.',
			error_long=u"Du kannst dich leider nur bist {}h vor der Schicht austragen. Sprich mit einem Organisator.".format(config.user_shift_unclaim_timeout_hours),
			config=config, session=request.session)
		
	## delete the assignment
	db.update('DELETE FROM person_schicht WHERE pers_id=? AND schicht_id=? ',
			(helferid, schicht_id))
	if tag != -1:
		return redirect('/schicht#tabs-%d' % tag)
	return redirect('/helfer/' + str(helferid))


## dinge über diese eine schicht
@expose('/schicht/<int:schicht_id>')
def schichtinfo(request, schicht_id):
	schichten = db.select("""SELECT
					schicht.*,
					station.name AS stationname,
					COUNT(DISTINCT person_schicht.schicht_id) AS have_persons
				FROM
					schicht
				LEFT JOIN
					person_schicht ON person_schicht.schicht_id = schicht.id
				JOIN
					station ON station.id = schicht.station_id
				WHERE
					schicht.id = ?
				GROUP BY
					schicht.id
				ORDER BY
					from_day ASC, from_hour ASC""", (schicht_id,))
	belegt = True
	if (is_user_logged_in(request.session)):
		belegt = db.select("""SELECT
					count(*) as belegt
				FROM
					schicht AS s
				INNER JOIN
					schicht AS s1
				ON
					((s1.from_day * 24 + s1.from_hour <= s.from_day * 24 + s.from_hour) AND
						(s1.until_day * 24 + s1.until_hour > s.from_day * 24 + s.from_hour)) OR
					((s1.from_day * 24 + s1.from_hour < s.until_day * 24 + s.until_hour) AND
						(s1.until_day * 24 + s1.until_hour >= s.until_day * 24 + s.until_hour)) OR
					((s1.from_day * 24 + s1.from_hour >= s.from_day * 24 + s.from_hour) AND
						(s1.until_day * 24 + s1.until_hour <= s.until_day * 24 + s.until_hour))
				INNER JOIN
					person_schicht AS ps ON ps.schicht_id = s1.id
				WHERE
					s.id = ? AND ps.pers_id = ?;""", (schicht_id,request.session['userid']))
		belegt = belegt[0][0]

	return render_template('schichtinfo.xml', schicht_id=schicht_id, schicht=schichten[0],
			belegt=belegt, session=request.session)

## übersicht über alle
@expose('/schicht')
@expose('/schichtplan/<int:userid>')
def schichtuebersicht(request, userid=None):
	schichten = db.select("""SELECT
					schicht.*,
					schicht.name AS aufgabe,
					station.id AS station_id,
					station.name AS stationname,
					COUNT(DISTINCT person_schicht.pers_id) AS have_persons,
					GROUP_CONCAT(DISTINCT person.username) AS persons,
					GROUP_CONCAT(DISTINCT person.id) AS person_ids
				FROM
					schicht
				LEFT JOIN
					person_schicht ON person_schicht.schicht_id = schicht.id
				LEFT JOIN
					person ON person_schicht.pers_id = person.id
				JOIN
					station ON station.id = schicht.station_id
				WHERE
				 	person.id = ? {}
				GROUP BY
					schicht.id
				ORDER BY
					from_day ASC, from_hour ASC""".format(" OR 1" if not userid else ""), #we explicitly want the 0 to evaluate to the sql injection
					(userid,))

	#ab hier wirds wirr, wie das bei einer 4D-Tabelle halt so ist :/
	#1. und 2. Dimension deklarieren
	tage = {}
	for schicht in schichten:

		def handleSchicht(schicht):
			fday = schicht["from_day"]

			#1. und 2. Dimension (tabs, zeilen) initialisieren, dritte deklarieren
			if fday not in tage.keys():
				tage[fday] = {}

				tage[fday]["schichten"] = [{} for i in range(0,25)] #hier werden die stunden/tag (x-achse) gespeichert
				tage[fday]["stationen"] = {} #hilfsobjekt: welche stationen gibt es/tag, wie viele aufgaben/station?

			tag = tage[fday]


			#wenn neuer wert in 3. dimension (stationen), diesen initialisieren, 4. deklarieren
			#verwendete stationen speichern
			if schicht["station_id"] not in tag["stationen"].keys():
				tag["stationen"][schicht["station_id"]] = []

				for hour in range(0,25):
					tag["schichten"][hour][schicht["station_id"]] = {}

			#wenn neuer wert in 4. dimension (aufgaben), diesen intialisieren
			#verwendete
			if schicht["aufgabe"] not in tag["stationen"][schicht["station_id"]]:
				tag["stationen"][schicht["station_id"]].append(schicht["aufgabe"])

				for hour in range(0,25):
					tag["schichten"][hour][schicht["station_id"]][schicht["aufgabe"]] = None

			maxHour = schicht["until_hour"]
			if not schicht["from_day"] == schicht["until_day"]:
				#mitternachtsuebergreifende schichten rekursiv behandeln
				maxHour = 24
				tmpSchicht = dict(schicht)
				tmpSchicht["from_day"] = tmpSchicht["from_day"]+1
				tmpSchicht["from_hour"] = 0
				handleSchicht(tmpSchicht)

			for hour in range(schicht["from_hour"],maxHour):
				#Wert in allen Dimensionen (tag, stunde, station, aufgabe) zuweisen
				tag["schichten"][hour][schicht["station_id"]][schicht["aufgabe"]] = schicht

		handleSchicht(schicht)

	station_sorted = db.select('SELECT s.id, s.name FROM station AS s ORDER BY s.sort ASC;');

	if is_user_logged_in(request.session):
		user_schichten = db.select("""SELECT
							res.id, ps.schicht_id
						FROM
							schicht AS res
						LEFT JOIN
							person_schicht AS ps, schicht AS s1 ON
							((res.from_day * 24 + res.from_hour <= s1.from_day * 24 + s1.from_hour) AND
								(res.until_day * 24 + res.until_hour > s1.from_day * 24 + s1.from_hour)) OR
							((res.from_day * 24 + res.from_hour < s1.until_day * 24 + s1.until_hour) AND
								(res.until_day * 24 + res.until_hour >= s1.until_day * 24 + s1.until_hour)) OR
							((res.from_day * 24 + res.from_hour >= s1.from_day * 24 + s1.from_hour) AND
								(res.until_day * 24 + res.until_hour <= s1.until_day * 24 + s1.until_hour))
						WHERE
							ps.pers_id = ? AND ps.schicht_id = s1.id;""", (request.session["userid"],))

		blocked_schichten = [x[0] for x in user_schichten]
		user_schichten = [x[1] for x in user_schichten]
		admin_mode = is_user_admin(request.session)
	else:
		user_schichten=[]
		blocked_schichten = []
		admin_mode = False

	rows = db.select('SELECT username, id FROM person')
	all_users = {}
	for r in rows:
		all_users[r['username']] = r['id']

	rows = db.select('SELECT * from schicht_order')
	schicht_order = {}
	for r in rows:
		schicht_order[r['schicht_name']] = r['sort']

	#import pprint
	#pp = pprint.PrettyPrinter(indent=4)
	#pp.pprint(tage)
	
	template = 'schichtplan.xml'
	username = None
	if not userid == None:
		username = db.select("SELECT username FROM person WHERE id = ?", (userid,))
		if len(username) > 0:
			username = username[0][0]
		else:
			return render_template('error.xml', error_short='wrong id',
				error_long="pfui, diese userid gibt es nicht!",
				config=config, session=request.session)
		template = "schichtplan_singleuser.xml"

	return render_template(template,
			schichten=schichten,
			tage = tage,
			session=request.session,
			admin_mode=admin_mode,
			all_users=all_users,
			user_schichten = user_schichten,
			blocked_schichten = blocked_schichten,
			username = username,
			station_sorted = station_sorted,
			sortingfunc = lambda x: schicht_order[x[0]])

