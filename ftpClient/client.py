import socket
import os
import sys
import getpass
import time

class myftpclient:

	def __init__(self, BUFFERSIZE=4096):
		self.ctrlSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.BUFFERSIZE = BUFFERSIZE

	def connect(self, host="portal.sjtu.edu.cn", port=21):
		self.ctrlSock.connect((host, port))
		self.printResponse()
		self.printResponse()

	def printResponse(self):
		response = self.ctrlSock.recv(self.BUFFERSIZE)
		print response

	def login(self):
		username = raw_input('Username: ')
		self.ctrlSock.send("USER %s\r\n" % username)
		self.printResponse()
		pwd = getpass.getpass('Password: ')
		self.ctrlSock.send("PASS %s\r\n" % pwd)
		self.printResponse()

	def run(self):
		while 1:
			cmd = raw_input("ftp>> ")
			res = self.ctrlSock.send(str(cmd)+"\r\n")
			self.printResponse()

if __name__ == "__main__":
	client = myftpclient()
	client.connect()
	client.login()
	client.run()