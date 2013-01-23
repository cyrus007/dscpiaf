#!/usr/bin/python
# Copyright 2013 Swapan Sarkar <swapan@yahoo.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''A script to interpret ContactID codes and send them onwards from
   asterisk'''

__author__ = 'swapan@yahoo.com'
__version__ = '0.0.1'

import os, sys, time
import glob, getopt
import ConfigParser
import twitter

execfile("alarm.inc")

class UsingTwitter(object):
    def __init__(self, key, secret, token_key, token_secret):
	self.api = twitter.Api(consumer_key=key,
			  consumer_secret=secret,
			  access_token_key=token_key,
			  access_token_secret=token_secret)

    def send(self, alarm_out):
	sendfile = open(alarm_out)
	status = self.api.PostUpdate(sendfile.read())


class UsingSendmail(object):
    def __init__(self, account, fromuser, touser):
	pass

    def send(self, alarm_out):
	pass


class UsingScreen(object):
    def __init__(self):
	pass

    def send(self, alarm_out):
	sendfile = open(alarm_out)
	for line in sendfile:
		print line
	sendfile.close()


class Alarm(object):
    def __init__(self):
	parser = ConfigParser.ConfigParser(allow_no_value=True)
	parser.read(glob.glob('/etc/asterisk/alarmreceiver.conf'))
	self.stampfmt = parser.get('general', 'timestampformat')      #"%a %b %d, %Y @ %H:%M:%S %Z"
	parser.read('/root/.alarmconf')
	self.protocol = parser.get('general', 'protocol')
	self.callerid = parser.get('general', 'callerid')
	self.callername = parser.get('general', 'callername')
	self.account = parser.get('general', 'account')
	self.payload = object
	if( parser.get('general', 'payload-type') == 'twitter' ):
		self.payload = UsingTwitter(parser.get('payload', 'consumerkey'), parser.get('payload', 'consumersecret'),
				       parser.get('payload', 'tokenkey'), parser.get('payload', 'tokensecret'))
	elif ( parser.get('general', 'payload-type') == 'sendmail' ):
		self.payload = UsingSendmail(parser.get('payload', 'account'), parser.get('payload', 'fromuser'), parser.get('payload', 'touser'))
	else:
		self.payload = UsingScreen()
	self.zones = []
	for i in range(1, 40):
		try:
			zone_text = parser.get('zones', 'Zone['+str(i)+']')
			self.zones.append( zone_text )
		except ConfigParser.NoOptionError:
			pass
	print self.zones
	print coid_action

    def parseEvents(self, alarm_dir='/var/spool/asterisk/alarm', alarm_out='/var/spool/asterisk/alarm/latest.txt'):
	try:
		eventfiles = glob.glob(alarm_dir + '/event-*')
		outfile = open(alarm_out, 'w')
		outfile.write("# Your security panel generated the following alarms\n\n")
	
		notifs = []
		parser = ConfigParser.ConfigParser(allow_no_value=True)
		for file in eventfiles:
       		 	parser.read(file)
			protocol = parser.get('metadata', 'PROTOCOL')
			if( protocol != self.protocol):
				print("Protocol mismatch: %s vs %s" % (protocol, self.protocol)) 
			callerid = parser.get('metadata', 'CALLINGFROM')
			if( callerid != self.callerid):
				print("Calling from mismatch: %s vs %s" % (callerid, self.callerid)) 
			callername = parser.get('metadata', 'CALLERNAME')
			if( callername != self.callername):
				print("Callername mismatch: %s vs %s" % (callerid, self.callerid)) 
			notifs.append({ 'timestamp' : parser.get('metadata', 'TIMESTAMP'),
			                'events' : parser.options('events') })
	 
		#Make replacements in content for each alarm code 
		for notif in notifs: 
			tstamp = time.strptime(notif['timestamp'], self.stampfmt)
			for event in notif['events']:
				if( event[0:4] != self.account):
					print("Account number mismatch: %s vs %s" % (event[0:3], self.account)) 
				if( event[4:6] != '18'):
					print("Message type mismatch: %s vs 18" % event[4:5]) 
				event_type  = int(event[6])
				event_code  = event[7:10]
				try:
					event_group = event[10:12]	#always 01 if present
				except:
					pass
				try:
					event_zone  = int(event[12:15])	#from 000 to 040
				except:
					pass
				print( "Event=%s (Type=%s : Zone=%s : Code=%s)\n" % (event, event_type, event_zone, event_code) )
				if( event_zone ):
					event_str = "@%s -> %s - %s alarm type: %s\n" % (time.strftime("%H:%M:%S", tstamp), self.zones[event_zone], coid_action[event_type], coid_codes[event_code])
				else:
					event_str = "@%s -> Supervisory alarm type: %s\n" % (time.strftime("%H:%M:%S", tstamp), coid_codes[event_code]) 
				outfile.write(event_str)
		for file in eventfiles:
			pass
#			os.del( file )
		outfile.close();
	except IOError as e:
		print( "Could not write to file '%s':I/O error(%i): %s\n" % (alarm_out, format(e.errno,e.strerror)))

    def send(self, outfile):
	self.payload.send(outfile)


def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd:o:", ["help", "folder=", "outfile="])
	except getopt.GetoptError:
		pass
	folder  = '/var/spool/asterisk/alarm'
	outfile = '/var/spool/asterisk/alarm/latest.txt'
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print( "%s [-h|--help] [-d|--folder <folder>] [-o|--outfile <file>]\n" % sys.argv[0] )                     
			sys.exit()                  
		elif opt in ("-d", "--folder"):
			folder = arg
		elif opt in ("-o", "--outfile"):
			outfile = arg
	myalarm = Alarm()
	myalarm.parseEvents(folder, outfile)
	myalarm.send(outfile)

if __name__ == '__main__':
	main()
