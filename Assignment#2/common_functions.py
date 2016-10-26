import socket, json, struct

# Purpose & Behavior: Encodes a message and then sends it to the defined socket.
# Input: Newly created object, and socket where TCP connection is created and the object that we
# want to send over.
# Output: None
def send_msg(sock, object):
	# serializing object into a JSON formatted stream and then encoded 
	# into a unicode string.
	send_msg_encoded = json.dumps(object).encode()
	send_msg_length = len(send_msg_encoded) # send message size 
	send_msg_length_encoded = struct.pack("!i", send_msg_length) # encodes an int as a 32-bit binary value; big-endian

	sock.sendall(send_msg_length_encoded) # sends encoded "message length"
	sock.sendall(send_msg_encoded) # sends encoded message

# Purpose & Behavior: Receives a message from the sender socket and decodes it. 
# Input: Newly created object, and socket where TCP connection is created.
# Output: None
def recv_msg(sock):
	# Receive at most msg_length bytes
	# Returns value received
	length_of_length = 4 # length of the (length of the received message)
	recvd_msg_length_encoded = sock.recv(length_of_length, socket.MSG_WAITALL) # reads the message's (from sending socket) length
	recvd_msg_length, = struct.unpack("!i", recvd_msg_length_encoded) # decodes the 32-bit binary value as an int; big-endian
	recvd_msg = sock.recv(recvd_msg_length, socket.MSG_WAITALL)# reads the message

	if (len(recvd_msg) == 0):
		# recv gives 0 result if the connection has been closed
		print("Connection terminated.") 
	elif (len(recvd_msg) != recvd_msg_length):
		print("Incomplete message.") 
	else:
		recvd_msg = recvd_msg.decode('utf-8') # decodes the received message
		return recvd_msg 