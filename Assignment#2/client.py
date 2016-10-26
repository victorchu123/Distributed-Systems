#!/usr/bin/python3
import socket, argparse, sys, common_functions

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

	def start(self):
		args = self.parse_cmd_arguments()
		sock = self.start_connection(args)
		args_dict = self.create_dict(args)

		# sends encoded message length and message to server; if can't throw's an error
		try:
			common_functions.send_msg(sock, args_dict)
		except: 
			print ("Failed send over whole message.")
			if (sock is not None):
	 			sock.close()
	 		sys.exit()

	 	# receives decoded message length and message from server; if can't throw's an error
	 	try: 
			recvd_msg = common_functions.recv_msg(sock)
			print (recvd_msg)
		except ConnectionResetError:
			print("Connection dropped.")
			sys.exit()
		except AttributeError:
			print ("Cannot decode message.")
			if (sock is not None):
 				sock.close()
 			sys.exit()

		if (sock is not None):
 			sock.close()
 		sys.exit()

if __name__ == '__main__':
	client = Client()
