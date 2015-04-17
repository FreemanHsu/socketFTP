import socket
import os
import struct
import sys

class mysocketclient:

	def __init__(self, MSGLEN=2048, sock=None):
		self.MSGLEN = MSGLEN
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		else:
			self.sock = sock

	def connect(self, host, port):
		self.sock.connect((host, port))
		response = self.myreceive()
		print response

	def mysend(self, msg):
		length = len(msg)
		if length>9999:
			print "Message too long\n"
			return False
		newstr = '<%5d>%s'%(length, msg)
		sent = self.sock.send(newstr)
		if sent == 0:
			print "Socket Connection has broken\n"
			return False
		return True

	def myreceive(self):
		s = self.sock.recv(7)
		if s == '':
			print "Socket Connection has broken\n"
			return ''
		length = int(s[1:-1])
		msg = self.sock.recv(length)
		return msg

	def run(self):
		while 1:
			cmd = raw_input(">> ")
			res = self.check_cmd(str(cmd))
			if res == 'Done':
				continue
			elif res == 'WaitForResponse':	
				response = self.myreceive()
				print response
			elif res == 'AppendOp':
				self.doAppend(str(cmd))
			elif res == 'GetOp':
				self.doGet(str(cmd))
			elif res == 'Exit':
				self.sock.close()
				break
			else:
				print 'Unknown Error\n'

	def check_cmd(self, cmd):
		pre_cmd = cmd.split(' ')[0]
		if pre_cmd == 'help':
			print '''1. ls : List the objects in current directory.
2. cd remote-dir : Change directory.
3. append local-file[remote-file] : Upload local file to remote,
\tif [remote-file] not specified, use the local-file name.
4. get remote-file[local-file] : Download remote-file to local,
\tif [local-file] not specified, use the remote-file name.
5. delete remote-file : Delete remote file.
6. pwd : Print the current working directory on remote.
7. bye : Quit the file client'''
			return 'Done'
		elif pre_cmd in ['ls', 'cd', 'delete', 'pwd']:
			self.mysend(cmd)
			return 'WaitForResponse'
		elif pre_cmd == 'append':
			return 'AppendOp'
		elif pre_cmd == 'get':
			return 'GetOp'
		elif pre_cmd == 'bye':
			return 'Exit'
		else:
			print 'Unknown Cmd, type in \'help\' for usage guide.'
			return 'Done'

	def doAppend(self, cmd):
		new_cmd = cmd
		cmds = cmd.split(' ')
		if len(cmds) == 1:
			filename = raw_input("File to transfer: ")
			new_cmd = 'append '+ str(filename)
		else:
			filename = cmds[1]
		if os.path.exists(filename) and os.path.isfile(filename):
			self.mysend(new_cmd)
		else:
			print 'No such file locally'
			return
		filesize = os.stat(filename).st_size
		fhead = struct.pack('128sL',filename.split('/')[-1], filesize)
		self.sock.send(fhead)
		fp = open(filename, 'rb')
		currentsize = 0
		while 1:
			filedata = fp.read(self.MSGLEN)
			if not filedata: break
			sent = self.sock.send(filedata)
			currentsize += sent
			sys.stdout.write("\r"+'#'*(currentsize*40/filesize)+'\t'+str(currentsize*100/filesize)+'%')
		print
		fp.close


	def doGet(self, cmd):
		new_cmd = cmd
		cmds = cmd.split(' ')
		if len(cmds) == 1:
			filename = raw_input("File to download: ")
			new_cmd = 'get '+ str(filename)
		self.mysend(new_cmd)
		if self.myreceive() == 'ReadyToSend':
			fhead = self.sock.recv(struct.calcsize('128sL'))
			filename, filesize = struct.unpack('128sL', fhead)
			filename = filename.strip('\00')
			if len(cmds) == 3:
				fp = open(cmds[2], 'wb')
			else:
				fp = open(os.path.join(os.getcwd(),filename), 'wb')
			restsize = filesize
			while 1:
				if restsize > self.MSGLEN:
					filedata = self.sock.recv(self.MSGLEN)
				else:
					filedata = self.sock.recv(restsize)
				if not filedata: break
				fp.write(filedata)
				restsize = restsize - len(filedata)
				sys.stdout.write("\r"+'#'*((filesize-restsize)*40/filesize)+'\t'+str((filesize-restsize)*100/filesize)+'%')
				if restsize == 0: break
			print
			fp.close()
		else:
			print "No such file"

if __name__ == '__main__':
	client = mysocketclient()
	client.connect('', 50001)
	client.run()