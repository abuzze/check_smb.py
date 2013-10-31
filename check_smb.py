#!/usr/bin/python
#Author: Christoph Miessler 2013
#use python 2.7.5
#checks if an smb share is reachable and writes a testfile on it

import sys
import getopt
import tempfile
import socket
from datetime import datetime
from smb.SMBConnection import SMBConnection

#Nagiosstatus
status = {'OK': 0, 'WARNING':1,'CRITICAL':2,'UNKOWN':3}

def Usage():
	'''Shows the basic usage of the script'''
	Version()
	print "Usage: "
	print sys.argv[0]," -H <Hostname (FQDN)> -S <Share> -u <username> -p <password> -w"
	print "-u <username>"
	print "-p <password>"
	print "Optional Parameters:"
	print "-w 	will try to write and read from the share"
	
def Version():
	print "Version: 0.1"

def SMB_Connect(host,sharename,user,password,folder,writeable):
	'''connects to a share with the given credentials and checks if it's writeable or not
		host: hostname (FQDN)
		sharename: Name of the share
		username: username
		password: password
		writeable: if set to True, it will check if the share is writeable
	'''

	check_passed=False
	check_file=''.join(['/', folder,'/nagioscheck.txt'])
	hostname = host.split('.')
	host_ip= socket.gethostbyname(host)
	conn = SMBConnection(user, password, socket.gethostname(), hostname[0], use_ntlm_v2 = True)
	try:
		conn.connect(host_ip, 139)
	except:
		print "Connection to Host failed"
		sys.exit(status['CRITICAL'])
	
	if conn.auth_result:

		#only check if share is listed
		if not writeable:
			shares = conn.listShares()
			for share in shares:
				if sharename == share.name:
					print "Found ",share.name
					check_passed = True
					break
		else:
			#schreiben
			check_value = "File Created from nagios "+str(datetime.now())
			file_obj = tempfile.NamedTemporaryFile()
			file_obj.write(check_value)
			file_obj.flush()
			file_obj.seek(0)
			try:
				conn.storeFile(sharename,  check_file, file_obj)
			except:
				check_passed=False
			file_obj.close()

			#lesen
			file_obj = tempfile.NamedTemporaryFile()
			try:
				file_attributes, filesize = conn.retrieveFile(sharename,  check_file, file_obj)
				file_obj.seek(0)
				file_content= file_obj.read()
				if file_content == check_value:
					check_passed=True
			except:
				check_passed=False
			file_obj.close()
			conn.close()
			
			 #file loeschen
			try:
				conn = SMBConnection(user, password, socket.gethostname(), hostname[0], use_ntlm_v2 = True)
			 	conn.connect(host_ip, 139)
			 	conn.deleteFiles(sharename, check_file)
			except Exception, e:
			 	check_passed=False
			
		conn.close()

	else:
		print "Auth failed"
	if check_passed:
		return True
	else:
		return False

def main(argv):
	password=	""
	username=	""
	sharename=	""
	hostname= 	""
	folder=		""
	writeable=	False
	try:
		opts, args = getopt.getopt(argv, "hvH:S:F:u:p:w",["help","version"])
	except getopt.GetoptError:
		Usage()
		sys.exit(status['CRITICAL'])
	for opt, arg in opts:
		if opt in ("-h","--help"):
			Usage()
			sys.exit(status['OK'])
		elif opt in ('-v',"--version"):
			Version()
			sys.exit(status['OK'])
		elif opt == '-H':
			hostname = arg
		elif opt == '-H':
			hostname = arg
		elif opt == '-S':
			sharename = arg
		elif opt == '-u':
			username = arg
		elif opt == '-p':
			password = arg
		elif opt == '-F':
			folder = arg 
		elif opt == '-w':
			writeable = True
	if SMB_Connect(hostname,sharename,username,password,folder,writeable):
		print "SMB Check ok"
		sys.exit(status['OK'])
	else:
		print "SMB Check failed"
		sys.exit(status['CRITICAL'])

if __name__ == "__main__":
	main(sys.argv[1:])
