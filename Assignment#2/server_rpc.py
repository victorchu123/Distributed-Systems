import common_functions, socket, view_leader

rpc_dict = {}

# Purpose & Behavior: Sets entry in rpc dict with the given key to the given value; 
# if the entry doesn't exist, then the entry will be added to the dict.
# Input: Given key and given value.
# Output: None
def set(key, value):
	rpc_dict[key] = value
	print ("Setting locally-stored value with key: " + str(key) + " to " + str(value) + ".")

# Purpose & Behavior: Gets the entry in rpc dict with the given key;
# if the entry doesn't exist, then display an error.
# Input: Given key that you want the value of.
# Output: Corresponding value to the given key.
def get(key):
	try:
		if (rpc_dict[key] is not None):
			print ("Returning value that corresponds with " + str(key) + ".")
			return rpc_dict[key]
	except LookupError:
		print ("Can't find a value with that key!")
		return None

# Purpose & Behavior: Prints out all keys with entries in the rpc dict;
# if there are none, then display an error.
# Input: None
# Output: A list of all keys that are in rpc dict.
def query_all_keys():
	keys_queried = []
	for key, value in rpc_dict.items():
		keys_queried.append(key)

	if (len(keys_queried) == 0):
		print ("No keys have been set yet!")
		return None	
	else:
		print ("Returning a list of keys that have been set by the RPC.")
		return keys_queried

def heartbeat(unique_id, port, ip):
	try:
		sock = socket.create_connection((ip, view_leader.src_port)) # opens connection with view leader
		print ('Connecting to viewleader...')
		heartbeat_tuple = (unique_id, port)
		common_functions.send_msg(sock, heartbeat_tuple) # sends heartbeat msg to view leader
		print ('Sending heartbeat msg...')
		recvd_msg = common_functions.recv_msg(sock)
		print ('Receiving response...')

		if (recvd_msg is not None):
			print (recvd_msg)

		sock.close()

	except Exception as e:
		print ('Heartbeat rejected, will try again in 10 seconds: ', e)

