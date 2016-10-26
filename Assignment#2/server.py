#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3
import socket, json, server_rpc, sys, common_functions, uuid

class Server:

	def __init__(self):
		self.src_port = 38000
		self.view_leader_ip = 'localhost'
		self.unique_id = uuid.uuid4()
		self.start()

	# Purpose & Behavior: Starts listening on the designated src port for a client. 
	# Input: Newly created object.
	# Output: Socket that is bound to src port.
	def start_listening(self, src_port):
		# tries to listen on ports 38000-38010; it will stop if it either finds an open port or gives up
		while (self.src_port <= 38010):
			print ("Trying to listen on "+ str(self.src_port) + '...')
			# Note these calls may throw an exception if it fails
			try: 
				bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				bound_socket.bind(('', self.src_port)) # binds socket to src port
				bound_socket.listen(1) # socket starts listening for client
				bound_socket.settimeout(10)
				break
			except:
				if (self.src_port < 38010):
					self.src_port += 1
				else:
					print ("Cannot find an open port from 38000-38010.")
					sys.exit()
				continue

		return bound_socket

	# Purpose & Behavior: Starts accepting client connections and deals with receiving/responding to messages.
	# Input: Newly created object, and socket that is bound to port 2806.
	# Output: None
	def accept_and_handle_messages(self, bound_socket, src_port, view_leader_ip):
		# Accept connections forever
		while True:
			try:
				sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
				if (accepted_port is not None): # checks if there is an accepted_port
					print ("Accepting connection from host " + addr)

					# receives decoded message length and message from client; if can't throw's an error
					try: 
						recvd_msg = json.loads(common_functions.recv_msg(sock)) # decodes JSON formatted stream into a dict
					except ConnectionResetError:
						print("Connection dropped.")
					except AttributeError:
						print ("Cannot decode message.")

					response_dict = self.process_msg_from_client(recvd_msg)

					# sends encoded message length and message to client; if can't throw's an error
					try: 
						common_functions.send_msg(sock, response_dict)
					except: 
						print ("Can't send over whole message.")
						sock.close()

			except socket.timeout as e:
				server_rpc.heartbeat(str(self.unique_id), self.src_port, self.view_leader_ip)
				continue

	# Purpose & Behavior: Processes commands from the received message and calls upon the 
	# appropriate functions in order to generate a response to the client.
	# Input: Newly created object, and received message in the form of a decoded dictionary.
	# Output: Dictionary that is the response to the client and will be sent to the client.
	def process_msg_from_client(self, recvd_msg):
		function_from_cmd = recvd_msg["cmd"] # takes function arguments from received dict
		unique_id = recvd_msg["id"] # takes unique_id from receieved dict
		# checks if function is print; if so, then take the text from the received dict
		if (function_from_cmd == "print"):
			text = recvd_msg["text"] # print's argument
			# text length will always be > 0; if text length == 1, 
			# then make text into string rather than a list.
			if (len(text) == 1):
				text = text[0]

			print ("Printing " + str(text))
			response_dict = {'status': 'success','result': text, 'id': unique_id}
		elif (function_from_cmd == "set"):
			server_rpc.set(recvd_msg["key"], recvd_msg["val"])
			response_dict = {'status': 'success', 'id': unique_id}
		elif (function_from_cmd == "get"):
			result = server_rpc.get(recvd_msg["key"])
			if (result is None):
				response_dict = {'status': 'fail', 'result': result, 'id': unique_id}
			else:
				response_dict = {'status': 'success', 'result': result, 'id': unique_id}
		elif (function_from_cmd == "query_all_keys"):
			result = server_rpc.query_all_keys()
			if (result is None):
				response_dict = {'status': 'fail', 'result': result, 'id': unique_id}
			else:
				response_dict = {'status': 'success', 'result': result, 'id': unique_id}
		else:
			print ("Rejecting RPC request because function is unknown.")

		return response_dict

	def start(self):
		bound_socket = self.start_listening(self.src_port)
		self.accept_and_handle_messages(bound_socket, self.src_port, self.view_leader_ip)
		sock.close() # closes connection with server

if __name__ == '__main__':
	server = Server()