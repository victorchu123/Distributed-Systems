rpc_dict = {}

# sets entry in rpc dict with the given key to the given value; 
# if entry doesn't exist, then add it to the dict.
def set(key, value):
	rpc_dict[key] = value
	print ("Setting locally-stored value with key: " + str(key) + " to " + str(value) + ".")

# gets the entry in rpc dict with the given key;
# if the entry doesn't exist, then display an error.
def get(key):
	try:
		if (rpc_dict[key] is not None):
			print ("Returning value that corresponds with " + str(key) + ".")
			return rpc_dict[key]
	except LookupError:
		print ("Can't find a value with that key!")
		return None

# prints out all keys with entries in the rpc dict;
# if there are none, display an error.
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
