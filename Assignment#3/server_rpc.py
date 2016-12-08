import common_functions

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
