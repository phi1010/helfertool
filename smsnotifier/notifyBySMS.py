#!/usr/bin/env python3

import sys
#sys.dont_write_bytecode = True

import sqlite3
import datetime
import urllib.parse, urllib.request

#make parent directory importable
import sys 
sys.path.append("..")

import config as config

#this class is a pseudo-dict that returns None for any character that is not a valid GSM
#character and raises an KeyError for everything else
class validGSMCharactersDict(dict):
	
	def __getitem__(self, key):
		r = key
		#Big parts of ASCII are allowed (characters, punctuation, basic symbols)
		if (r >= ord(' ') and r <= ord('Z')) or (r >= ord('a') and r<= ord('z')):
			raise KeyError

		#Some special characters are allowed as well
		specChar = ['¥', '£', '¤', 'è', 'é', 'ù', 'ì', 'ò', 'Ç', 'Ø', 'ø', 'Å', 'å', 'Δ', '_', 'Φ', 'Γ', 'Λ', 'Ω', 'Π', 'Ψ', 'Σ', 'Θ', 'Ξ', 'Æ', 'æ', 'É', '¡', 'Ä', 'Ö', 'Ñ', 'Ü', '§', 'ä', 'ö', 'ñ', 'ü', 'à', '€', '\n', '\r']

		for char in specChar:
			if r == ord(char):
				raise KeyError

		#Remove character if not allowed
		return None

class SMSNotifier():
	
	def __init__(self, key):
		self.key = key
		self.request_url = "http://gateway.smstrade.de/?key={}&route=basic".format(key)
	
	def urlEncode(self, 	string):
		return urllib.parse.quote(string)
	

	def getSMSLength(self, sms):
		smsLength = len(sms)

		#Some characters need two byte in GSM encoding
		twoByteCharacters = ["€", "[", "]", "{", "}", "~", "|", "^", "\\"]

		for tbc in twoByteCharacters:
			smsLength += sms.count(tbc)
		
		return smsLength
	

	def sendSMS(self, sms, number):
		#print("sms to {}: {}".format(number, sms))

		#Remove characters that are not in GSM encoding
		gsmLine = sms.translate(validGSMCharactersDict())

		#print("connecting to: {}&charset=UTF8&to={}&message={}".format(self.request_url,number,self.urlEncode(gsmLine)))
		
		response = urllib.request.urlopen("{}&charset=UTF8&to={}&message={}".format(self.request_url,number,self.urlEncode(gsmLine)))

		if response == None:
			print("sms query to smsgateway failed")
			return
		
		responseCode = str( response.read(), encoding='utf8' )
		
		if not "100" in responseCode:
			print("sms gateway issued an error: {}".format(responseCode))
		
		
		
if __name__ == "__main__":
	
	
	notifier = SMSNotifier("APIKEYGOESHERE")
	
	
	conn = sqlite3.connect(config.dbfilename, detect_types=sqlite3.PARSE_DECLTYPES)
	conn.execute('pragma foreign_keys=ON;')
	conn.execute('pragma encoding = "UTF-8";')
	conn.row_factory = sqlite3.Row
	
	cur = conn.cursor()
	
	cur.execute("""SELECT 
				*,
				schicht.name AS schichtname,
				station.name AS stationsname
			 FROM 
			 	schicht
			 JOIN 
			 	person_schicht ON schicht.id = person_schicht.schicht_id
			 JOIN
			 	person ON person_schicht.pers_id = person.id
			 JOIN
				station ON station.id = schicht.station_id
			 WHERE
			 	person.mobile != ""
			 """)
	
	matches = cur.fetchall()
		
	daysSinceStart =  (datetime.date.today()-config.start_date).days
	curHours = datetime.datetime.time(datetime.datetime.now()).hour
	
	now = daysSinceStart*24 + curHours
	for res in matches:
		if res["from_day"]*24 + res["from_hour"] == daysSinceStart*24 + curHours + 1: # +1 wg angefangene Stunde
		
			msg = "Hi {}! Deine Schicht '{}' faengt um {} Uhr an. Bitte sei rechtzeitig an der Station '{}'. Danke & viel Spass!"\
				.format(res["username"], res["name"], res["from_hour"], res["stationsname"])
			#print("SMS an {} gesendet: {}".format(res["mobile"], msg))
	
			notifier.sendSMS(msg, res["mobile"])
	
	conn.close()

