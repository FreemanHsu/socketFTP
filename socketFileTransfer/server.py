import socket
import os
import select
import struct

class mysocketserver:

	def __init__(self, MSGLEN=2048, sock=None):
		self.MSGLEN = MSGLEN
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.sock = sock

		self.base_dir = os.path.join(os.getcwd(), 'ftpbase')
		if not os.path.exists(self.base_dir):
			os.system('mkdir ftpbase')

		self.cwd = {}

	def setup(self, host, port):
		self.sock.bind((host, port))
		self.sock.listen(5)
		self.descriptors = [self.sock]
		print "Socket Server Started on port %s" % port

	def my_server_send(self, remsock, msg):
		length = len(msg)
		if length>9999:
			print "Message too long"
			return False
		newstr = '<%5d>%s'%(length, msg)
		sent = remsock.send(newstr)
		if sent == 0:
			remhost, remport = remsock.getpeername()
			print "Socket Connection with (%s, %s) has broken" % (remhost, remport)
			return False
		return True

	def my_server_receive(self, remsock):
		s = remsock.recv(7)
		if s == '':
			remhost, remport = remsock.getpeername()
			print "Socket Connection with (%s, %s) has broken" % (remhost, remport)
			return ''
		length = int(s[1:-1])
		msg = remsock.recv(length)
		return msg

	def run(self):
		while 1:
			# Await an event on a readable socket descriptor
			(ready_to_read, ready_to_write, in_error) = select.select(self.descriptors, [], [])
			for sock in ready_to_read:
				# Open a new connection for client
				if sock == self.sock:
					self.accept()
				else:
					# Read something from the client
					sockstr = self.my_server_receive(sock)
					if sockstr == '':
						sock.close()
						self.descriptors.remove(sock)
					else:
						self.parse_the_cmd(sock, sockstr)

	def accept(self):
		newsock, (remhost, remport) = self.sock.accept()
		self.descriptors.append(newsock)
		self.cwd[newsock] = ''

		self.my_server_send(newsock, "You are connected to the socket file server")
		print "Client (%s %s) has connected to the server" % (remhost, remport)

	def parse_the_cmd(self, remsock, cmd):
		remhost, remport = remsock.getpeername()
		print "(%s, %s) sent the cmd %s" % (remhost, remport, cmd)
		
		pre_cmd = cmd.split(' ')[0]
		if pre_cmd == 'ls':
			self.my_server_send(remsock, ' '.join(os.listdir(os.path.join(self.base_dir, self.cwd[remsock]))))
		elif pre_cmd == 'pwd':
			self.my_server_send(remsock, '/'+self.cwd[remsock])
		elif pre_cmd == 'cd':
			cmds = cmd.split(' ')
			if len(cmds) == 1:
				self.cwd[remsock] = ''
				self.my_server_send(remsock, 'ok')
			else:
				# Not perfect here, quite a mess actually
				# Ignore leading '/'s for security problem
				# cd '/' works
				if cmds[1] == '.':
					self.my_server_send(remsock, 'ok')
				elif cmds[1] == '..':
					self.cwd[remsock] = '/'.join(self.cwd[remsock].split('/')[:-1])
					self.my_server_send(remsock, 'ok')
				else:
					while cmds[1][0] == '/' and len(cmds[1])>1:
						cmds[1] = cmds[1][1:]
					if cmds[1] == '/':
						self.cwd[remsock] = ''
						self.my_server_send(remsock, 'ok')
					elif os.path.exists(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),cmds[1])) and \
						 os.path.isdir(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),cmds[1])):
						if self.cwd[remsock] == '':
							self.cwd[remsock] = cmds[1]
						else:
							tmp = self.cwd[remsock].split('/')
							tmp.append(str(cmds[1]))
							self.cwd[remsock] = '/'.join(tmp)
						self.my_server_send(remsock, 'ok')
					else:
						self.my_server_send(remsock, 'no such directory')
		elif pre_cmd == 'delete':
			cmds = cmd.split(' ')
			if len(cmds) == 1:
				self.my_server_send(remsock, 'usage: delete remote-file')
			else:
				# Ignore leading '/'s for security problem
				while cmds[1][0] == '/' and len(cmds[1])>1:
					cmds[1] = cmds[1][1:]
				if os.path.exists(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),cmds[1])) and \
				   os.path.isfile(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),cmds[1])):
					os.remove(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),cmds[1]))
					self.my_server_send(remsock, 'ok')
				else:
					self.my_server_send(remsock, 'no such file')
		elif pre_cmd == 'append':
			self.doAppendServer(remsock, cmd)
		elif pre_cmd == 'get':
			self.doGetServer(remsock, cmd)

	def doAppendServer(self, remsock, cmd):
		cmds = cmd.split(' ')
		newfilename = None
		if len(cmds) == 3:
			newfilename = cmds[2]
		fhead = remsock.recv(struct.calcsize('128sL'))
		filename, filesize = struct.unpack('128sL', fhead)
		filename = filename.strip('\00')
		if newfilename is None:
			fp = open(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),filename), 'wb')
		else:
			fp = open(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),newfilename), 'wb')
		restsize = filesize
		while 1:
			if restsize > self.MSGLEN:
				filedata = remsock.recv(self.MSGLEN)
			else:
				filedata = remsock.recv(restsize)
			if not filedata: break
			fp.write(filedata)
			restsize = restsize - len(filedata)
			if restsize == 0: break
		fp.close()

	def doGetServer(self, remsock, cmd):
		cmds = cmd.split(' ')
		filename = cmds[1]
		if os.path.exists(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),filename)) and \
		   os.path.isfile(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),filename)):
			self.my_server_send(remsock,'ReadyToSend')
		else:
			self.my_server_send(remsock,'NothinToSend')
			return
		filesize = os.stat(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),filename)).st_size
		fhead = struct.pack('128sL',filename, filesize)
		remsock.send(fhead)
		fp = open(os.path.join(os.path.join(self.base_dir, self.cwd[remsock]),filename), 'rb')
		while 1:
			filedata = fp.read(self.MSGLEN)
			if not filedata: break
			remsock.send(filedata)
		fp.close

if __name__ == '__main__':
	server = mysocketserver()
	server.setup('', 50001)
	server.run()
