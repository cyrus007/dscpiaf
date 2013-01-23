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
import glob
import ConfigParser
import twitter

class UsingTwitter(object):
    def __init__(self, key, secret, token_key, token_secret):
	self.api = twitter.Api(consumer_key=key,
			  consumer_secret=secret,
			  access_token_key=token_key,
			  access_token_secret=token_secret)

    def send(self):
	sendfile = open(sys.argv[2])
	status = self.api.PostUpdate(sendfile.read())


class UsingSendmail(object):
    def __init__(self, account):
	pass

    def send(self):
	pass


class Alarm(object):
    def __init__(self):
	parser = ConfigParser.ConfigParser(allow_no_value=True)
	parser.read(glob.glob('/etc/asterisk/alarmreceiver.conf'))
	self.stampfmt = parser.get('general', 'timestampformat')      #"%a %b %d, %Y @ %H:%M:%S %Z"
	parser.read(glob.glob('~/.alarmconf'))
	self.protocol = parser.get('general', 'protocol')
	self.callerid = parser.get('general', 'callerid')
	self.callername = parser.get('general', 'callername')
	self.account = parser.get('general', 'account')
	self.payload = object
	if( parser.get('general', 'payload-type') == 'twitter' ):
		self.payload = Twitter(parser.get('payload', 'consumerkey'), parser.get('payload', 'consumersecret'),
				       parser.get('payload', 'tokenkey'), parser.get('payload', 'tokensecret'))
	elif ( parser.get('general', 'payload-type') == 'sendmail' ):
		self.payload = Sendmail(parser.get('payload', 'account'), parser.get('payload', 'fromuser'), parser.get('payload', 'touser'))
	else:
		self.payload = Sendmail('localhost', 'pbx@localhost', 'root@localhost')
	self.zones = []
	self.zones[0] = ''
	for i in range(1, 40):
		self.zones[i] = parser.get('zones', 'Zone['+i+']')

    def parseEvents(self):
	try:
		#infile = '/var/spool/asterisk/alarm/event-!@#$%^'; 
		eventfiles = glob.glob(sys.argv[1] + '/event-*')
		#outfile = '/var/spool/asterisk/alarm/latest.txt'; 
		outfile = open(sys.argv[2], 'w')
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
				if( event[0:3] != self.account):
					print("Account number mismatch: %s vs %s" % (event[0:3], self.account)) 
				if( event[4:5] != coid_mt):
					print("Message type mismatch: %s vs %s" % (event[4:5], coid_mt)) 
				event_type  = event[6]
				event_code  = event[7:9]
				try:
					event_group = event[10:11]	#always 01 if present
				except:
					pass
				try:
					event_zone  = int(event[12:14])	#from 000 to 040
				except:
					pass
				if( event_zone ):
					event_str = "@%s -> %s - %s alarm type: %s\n" % (tstamp.strftime("%H:%M%S"), self.zones[event_zone], coid_action[event_type], coid_code[event_code]); 
				else:
					event_str = "@%s -> Supervisory alarm type: %s\n" % (tstamp.strftime("%H:%M%S"), coid_code[event_code]); 
				outfile.write(event_str)
		for file in eventfiles:
			pass
#			os.del( file )
	except IOError as e:
		print( "Could not write to file '%s':I/O error(%i): %s\n" % (sys.argv[2], format(e.errno,e.strerror)))
	finally:
		outfile.close();

    def send(self):
	self.payload.send()


def main():
	if (len(sys.argv) < 3):
		sys.exit("Usage: %s <alarm-files directory> <output file>\n" % sys.argv[0])
	myalarm = Alarm()
	myalarm.parseEvents()
	myalarm.send()

if __name__ == '__main__':
	main()
