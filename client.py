#!/usr/bin/python3
import socket, argparse, json, struct

# Purpose & Behavior: Uses argparse to process command line arguments into functions 
# and their respective inputs. 
# Input: None
# Output: namespace of command line arguments
def parse_cmd_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('--server', default='10.0.2.6')

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
# Input: command line argument namespace (args)
# Output: Socket where TCP connection is created.
def start_connection(args):
	# if the optional argument "--server" is used, 
	# then set localhost as this computer's IP.
	if (args.server is not None):
		if (args.server == 'localhost'):
			dest_host = '10.0.2.4'
		else:
			dest_host = args.server

	dest_port = 2806 # destination port; where TCP connection with server is established
	sock = socket.create_connection((dest_host, dest_port)) # opens connection with server at dest_host:dest_port or throws an exception
	if sock is None:
 		print("Can’t connect.")

	print('Trying to connect to ' + dest_host + ':' + str(dest_port))
	return sock

# Purpose & Behavior: Creates a dictionary from the provided namespace; 
# deletes unnecessary entries and adds unique id entry to the dict.
# Input: command line argument namespace (args)
# Output: Dictionary with relevant entries with keys (unique id, cmd, (key/text/val) depending on cmd)
def create_dict(args):
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
# Input: Socket where TCP connection is created and the dictionary with relevant 
# entries with keys (unique id, cmd, (key/text/val) depending on cmd)
# Output: None
def send_to_server(sock, args_dict):
	# serializing dict into a JSON formatted stream and then encoded 
	# into a unicode string.
	send_msg_encoded = json.dumps(args_dict).encode()

	send_msg_length = len(send_msg_encoded) # send message size 
	send_msg_length_encoded = struct.pack("!i", send_msg_length) # encodes an int as a 32-bit binary value; big-endian

	sock.sendall(send_msg_length_encoded) # sends encoded "message length" to server

	sock.sendall(send_msg_encoded) # sends encoded message to server

# Purpose & Behavior: Receives a message from the server and decodes it. 
# Input: Socket where TCP connection is created.
# Output: None
def recv_from_server(sock):

	# Receive at most msg_length bytes
	# Returns value received
	length_of_length = 4 # length of the (length of the received message)
	recvd_msg_length_encoded = sock.recv (length_of_length, socket.MSG_WAITALL) # reads the message's (from client) length
	recvd_msg_length, = struct.unpack("!i", recvd_msg_length_encoded) # decodes the 32-bit binary value as an int; big-endian
	recvd_msg = sock.recv(recvd_msg_length, socket.MSG_WAITALL)# reads the message from client

	if (len(recvd_msg) == 0):
		# recv gives 0 result if the connection has been closed
		print("Connected terminated") 
	elif (len(recvd_msg) != recvd_msg_length):
		print("Incomplete message") 
	else:
		recvd_msg = recvd_msg.decode() # decodes the message from server
		print(recvd_msg) # prints out response from server; in the format of {'status': some_str, 'result': some_str, 'id': some_str} 

# Purpose & Behavior: Main function.
# Input: None
# Output: None
def main():
	args = parse_cmd_arguments()
	sock = start_connection(args)
	args_dict = create_dict(args)
	send_to_server(sock, args_dict)
	recv_from_server(sock)
	sock.close() # closes connection with server

main()
