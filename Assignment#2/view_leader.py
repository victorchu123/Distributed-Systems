#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3

import time, server, common_functions, sys, socket, json

global view
view = []
global epoch
epoch = 0
global src_port
src_port = 39000

class ViewLeader():

	def __init__(self):
		self.heartbeats = {}
		self.start()

	def start(self):
		sock = self.start_listening()
		self.accept_heartbeat(sock)

	# Purpose & Behavior: Starts listening on the designated src port for a client. 
	# Input: Newly created object.
	# Output: Socket that is bound to src port.
	def start_listening(self):
		global src_port
		# tries to listen on ports 39000-39010; it will stop if it either finds an open port or gives up
		while (src_port <= 39010):
			print ("Trying to listen on "+ str(src_port) + '...')
			# Note these calls may throw an exception if it fails
			try: 
				bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				bound_socket.bind(('', src_port)) # binds socket to src port
				bound_socket.listen(1) # socket starts listening for client
				bound_socket.settimeout(5)
				break
			except Exception as e:
				if (src_port < 39010):
					src_port += 1
				else:
					print ("Cannot find an open port from 39000-39010: ", e)
					sys.exit()
				continue
		return bound_socket

	# Purpose & Behavior:
	# Input: 
	# Output:
	def accept_heartbeat(self, bound_socket):
		# Accept connections forever
		while True:
			try:
				sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
				if (accepted_port is not None): # checks if there is an accepted_port
					recvd_msg = common_functions.recv_msg(sock)
					new_id, port = json.loads(recvd_msg) # decodes JSON formatted stream
					heartbeats_value = (time.time(), 'working', new_id)

					if ((addr, port) in self.heartbeats):
						last_timestamp, status, current_id = self.heartbeats[(addr, port)]

						if (new_id == current_id):		
							if (status == 'working'): 
								print ("Accepting heartbeat from host: " + addr + ":" + str(port))
								common_functions.send_msg(sock, "Heartbeat was accepted.")
								self.heartbeats[(addr, port)] = heartbeats_value
							else:
								print ("Rejecting heartbeat from host: " + addr + ":" + str(port) + " because server failed.")
								common_functions.send_msg(sock, "Heartbeat was rejected.")
						else: 
							print ("Accepting heartbeat from host: " + addr + ":" + str(port))
							common_functions.send_msg(sock, "Heartbeat was accepted.")
							self.heartbeats[(addr, port)] = heartbeats_value
					else:
						print ("Accepting heartbeat from host: " + addr + ":" + str(port))
						common_functions.send_msg(sock, "Heartbeat was accepted.")
						self.heartbeats[(addr, port)] = heartbeats_value
				self.update_view()
			except socket.timeout as e:
				self.update_view()
				continue

	def update_view(self):
		global view
		global epoch

		failed_servers = []

		for key, value in self.heartbeats.items():
			if (time.time() - value[0] > 30) and (value[1] == 'working'):
				print ("It has been more than 30 seconds since last heartbeat, marking server as failed.")
				failed_servers.append(key)

		for server in failed_servers:
			last_timestamp, status, current_id = self.heartbeats[server]
			self.heartbeats[server] = (last_timestamp, 'failed', current_id)	

		# print (self.heartbeats)

		for key, value in self.heartbeats.items():
			if (value[1] == 'working') and (key not in view):
				view.append(key)
				epoch += 1
			elif (value[1] == 'failed') and (key in view):
				view.remove(key)
				epoch += 1

		if (epoch != 0) and (len(view) != 0):
			print (view, epoch)
		

def get_viewleader_info():
	info = []
	for addr, port in view:
		info.append(addr + ':' + str(port))
	return ('Active servers: ' + str(info), 'Current epoch: ' + str(epoch))

if __name__ == '__main__':
	view_leader = ViewLeader()