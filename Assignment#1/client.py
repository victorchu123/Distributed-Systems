#!/usr/bin/python3
import socket, argparse, json, struct, sys

class Client:

	def __init__(self): 
		self.start()

	# Purpose & Behavior: Uses argparse to process command line arguments into functions 
	# and their respective inputs. 
	# Input: Newly created object.
	# Output: namespace of command line arguments
	def parse_cmd_arguments(self):
		parser = argparse.ArgumentParser()
		parser.add_argument('--server', default='localhost')

		subparsers = parser.add_subparsers(dest='cmd')

		parser_set = subparsers.add_parser('set')
		parser_set.add_argument('key', type=str)
		parser_set.add_argument('val', type=str)

		parser_get = subparsers.add_parser('get')
		parser_get.add_argument('key', type=str)

		parser_print = subparsers.add_parser('print')
		parser_print.add_argument('text', nargs="*")

		parser_query = subparsers.add_parser('query_all_keys')

		args = parser.parse_args()
		return args

	# Purpose & Behavior: Starts TCP connection from this client to given server
	# Input: Newly created object, and command line argument namespace (args)
	# Output: Socket where TCP connection is created.
	def start_connection(self, args):
		# if the optional argument "--server" is used, 
		# then set localhost as this computer's IP. else, return error and exit.
		if (args.server is not None):
			if (args.cmd is None):
				print ("RPC command not provided.")
				sys.exit()
			
		dest_host = str(args.server)
		dest_port = 38000 # destination port; where TCP connection with server is established
		sock = None
		timeout = 5

		# tries to connect to dest_port; will continue until it either finds an open port or gives up
		while (dest_port <= 38010):
			print('Trying to connect to ' + dest_host + ':' + str(dest_port) + '...')
			try:
				sock = socket.create_connection((dest_host, dest_port), timeout) # opens connection with server at dest_host:dest_port
				break
			except: 
				dest_port = dest_port + 1
				continue
		if sock is None:
			print("Can’t establish a connection.")
			sys.exit()
		return sock

	# Purpose & Behavior: Creates a dictionary from the provided namespace; 
	# deletes unnecessary entries and adds unique id entry to the dict.
	# Input: Newly created object, and command line argument namespace (args)
	# Output: Dictionary with relevant entries with keys (unique id, cmd, (key/text/val) depending on cmd)
	def create_dict(self, args):
		args_dict = vars(args) # converts args namespace to a dict
		keys_to_delete = []

		# removes "server" key from dict, 
		# so we only send over the necessary arguments.
		for key, value in args_dict.items():
			if (key == "server"):
				keys_to_delete.append(key)

		for key in keys_to_delete:
			del args_dict[key]

		request_id = 0 # creates a unique id for the RPC
		args_dict["id"] = request_id # adds entry to args_dict with the "id" key

		return args_dict

	# Purpose & Behavior: Encodes a message and then sends it to the defined server. 
	# Input: Newly created object, and socket where TCP connection is created and the dictionary with relevant 
	# entries with keys (unique id, cmd, (key/text/val) depending on cmd)
	# Output: None
	def send_to_server(self, sock, args_dict):
		# serializing dict into a JSON formatted stream and then encoded 
		# into a unicode string.
		send_msg_encoded = json.dumps(args_dict).encode()
		send_msg_length = len(send_msg_encoded) # send message size 
		send_msg_length_encoded = struct.pack("!i", send_msg_length) # encodes an int as a 32-bit binary value; big-endian

		try:
			sock.sendall(send_msg_length_encoded) # sends encoded "message length" to server
			sock.sendall(send_msg_encoded) # sends encoded message to server
		except:
			print ("Failed send over whole message.")
			if (sock is not None):
	 			sock.close()
	 			sys.exit()

	# Purpose & Behavior: Receives a message from the server and decodes it. 
	# Input: Newly created object, and socket where TCP connection is created.
	# Output: None
	def recv_from_server(self, sock):
		# Receive at most msg_length bytes
		# Returns value received
		length_of_length = 4 # length of the (length of the received message)
		try:
			recvd_msg_length_encoded = sock.recv(length_of_length, socket.MSG_WAITALL) # reads the message's (from client) length
			recvd_msg_length, = struct.unpack("!i", recvd_msg_length_encoded) # decodes the 32-bit binary value as an int; big-endian
			recvd_msg = sock.recv(recvd_msg_length, socket.MSG_WAITALL)# reads the message from client
		except ConnectionResetError:
			print("Connection dropped.")
			sys.exit()

		if (len(recvd_msg) == 0):
			# recv gives 0 result if the connection has been closed
			print("Connection terminated.") 
			if (sock is not None):
	 			sock.close()
	 			sys.exit()
		elif (len(recvd_msg) != recvd_msg_length):
			print("Incomplete message.") 
			if (sock is not None):
	 			sock.close()
	 			sys.exit()
		else:
			try:
				recvd_msg = recvd_msg.decode() # decodes the message from server
			except:
				print ("Cannot decode message.")
				if (sock is not None):
	 				sock.close()
	 				sys.exit()
			print(recvd_msg) # prints out response from server; in the format of {'status': some_str, 'result': some_str, 'id': some_str} 

	def start(self):
		args = self.parse_cmd_arguments()
		sock = self.start_connection(args)
		args_dict = self.create_dict(args)
		self.send_to_server(sock, args_dict)
		self.recv_from_server(sock)
		sock.close() # closes connection with server

if __name__ == '__main__':
	client = Client()
