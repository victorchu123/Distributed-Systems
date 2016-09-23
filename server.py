#!/usr/bin/python3
import socket, struct, json, functions

# Purpose & Behavior: Starts listening on the designated port for a client. 
# Input: None
# Output: Socket that is bound to port 2806.
def start_listening():
	# Listen on port 2806 on all interfaces
	port = 2806
	bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Note these calls may throw an exception if it fails
	try: 
		bound_socket.bind(('', port)) # binds socket to port 2806
		bound_socket.listen(1) # socket starts listening for client
		print ("Trying to listen on "+ str(port) + '...')
	except:
		print ("Connection lost or failed to establish.")

	return bound_socket

# Purpose & Behavior: Starts accepting client connections and deals with receiving/responding to messages.
# Input: Socket that is bound to port 2806.
# Output: None
def accept_and_handle_messages(bound_socket):
	# Accept connections forever
	while True :
		sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection

		if (accepted_port is not None): # checks if there is an accepted_port
			print ("Connected to " + addr + ":" + str(accepted_port))
			recvd_msg = recv_from_client(sock)
			response_dict = process_msg_from_client(recvd_msg)
			send_to_client(sock, response_dict)

# Purpose & Behavior: Receives message from client and decodes it into a usuable dict.
# Input: Socket from accepted connection.
# Output: Received message in the form of a decoded dictionary.
def recv_from_client(sock):
	recvd_msg_length_encoded = sock.recv (4, socket.MSG_WAITALL) # reads the length of the encoded, received message
	recvd_msg_length, = struct.unpack("!i", recvd_msg_length_encoded) # decodes the encoded length
	recvd_msg = sock.recv(recvd_msg_length, socket.MSG_WAITALL).decode() # reads and decodes the received message
	recvd_msg = json.loads(recvd_msg) # decodes JSON formatted stream into a dict

	return recvd_msg

# Purpose & Behavior: Processes commands from the received message and calls upon the 
# appropriate functions in order to generate a response to the client.
# Input: Received message in the form of a decoded dictionary.
# Output: Dictionary that is the response to the client and will be sent to the client.
def process_msg_from_client(recvd_msg):
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
		functions.set(recvd_msg["key"], recvd_msg["val"])
		response_dict = {'status': 'success', 'id': unique_id}
	elif (function_from_cmd == "get"):
		result = functions.get(recvd_msg["key"])
		if (result is None):
			response_dict = {'status': 'fail', 'result': result, 'id': unique_id}
		else:
			response_dict = {'status': 'success', 'result': result, 'id': unique_id}
	else:
		result = functions.query_all_keys()
		if (result is None):
			response_dict = {'status': 'fail', 'result': result, 'id': unique_id}
		else:
			response_dict = {'status': 'success', 'result': result, 'id': unique_id}

	return response_dict

# Purpose & Behavior: Encodes given dictionary into a serialized unicode string 
# and sends it to the client.
# Input: Socket from accepted connection, and the dictionary that is the response 
# to the client and will be sent to the client.
# Output: None
def send_to_client(sock, response_dict):
	# checks if response_dict is non-empty
	if (response_dict is not None):
		send_msg = json.dumps(response_dict).encode() # turns response_dict into a JSON formatted stream and then encodes it

	send_msg_length = len(send_msg) # send message size 
	send_msg_length_encoded = struct.pack("!i", send_msg_length) #encodes an int as a 32-bit binary value; big-endian

	# sends encoded message length and message to client
	sock.sendall(send_msg_length_encoded)
	sock.sendall(send_msg)

# Purpose & Behavior: Main function.
# Input: None
# Output: None
def main():
	bound_socket = start_listening()
	accept_and_handle_messages(bound_socket)
	sock.close() # closes connection with server

main()