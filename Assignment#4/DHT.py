import hashlib, uuid

replica_count = 0
bucket_count = 0
HASH_MAX = 160
view_to_use = {}


# Purpose & Behavior: Hashes given key with SHA1 algorithm
# Input: key
# Output: hash number
def hash_key(d):
    d_encoded = d.encode('utf-8')
    sha1 = hashlib.sha1(d_encoded)
    # print ("HASH_MAX : {}".format(HASH_MAX))
    try:
        return int(sha1.hexdigest(), 16) % HASH_MAX
    except ZeroDivisionError as e:
        print ("Cannot mod by 0: ", e)

# Purpose & Behavior: Checks if given value is in the dictionary
# Input: value, dictionary
# Output: True/False
def is_val_in_dict(dictionary, val):
    for key, value in dictionary.items():
        if (dictionary[key] == val):
            return True
    return False

# Purpose & Behavior: Creates a distributed hash table in the form of {server_hash: ((addr, port), server_id)} for all replica servers
# Input: None
# Output: DHT
def create_DHT():
    server_dict = {}

    global replica_count
    if (len(view_to_use) >= 3):
        replica_count = 3
    else:
        replica_count = len(view_to_use)
        
    # adds active servers from view_to_use to DHT with new hashes
    for (addr, port, server_id), timestamp in view_to_use.items():
        if (len(server_dict) < replica_count): 
            # print ("Server ID: {}".format(server_id))
            server_hash = hash_key(server_id)
            # print ("Server Hash: {}".format(server_hash))
            server_dict[server_hash] = ((addr, port), server_id)

    # print ("Server Dict: {}".format(server_dict))
    return server_dict

# Purpose & Behavior: adds consecutive buckets (i.e. secondary and tertiary buckets) after the primary bucket has been determined
# Input: bucket counter, replica counter, list of ordered server hashes, DHT, replica buckets list
# Output: modified replica buckets list
def add_consecutive_buckets(bucket_count, replica_count, server_hashes_in_order, server_dict, replica_buckets):
    i = 0
    while (bucket_count < replica_count):
        ith_server_hash = server_hashes_in_order[i] 
        ith_dict_elem = server_dict[ith_server_hash]
        replica_buckets.append(ith_dict_elem)
        bucket_count += 1
        i += 1
    return replica_buckets

# Purpose & Behavior: Determines proper replica buckets from the given key and view
# Input: key and view
# Output: final replica buckets list
def bucket_allocator(key, view):
    global view_to_use
    view_to_use = view
    # print ("View to use: {}".format(view_to_use))
    server_dict = create_DHT() #update DHT
    key_hash = hash_key(key)

    # print ("View to use after update: {}".format(view_to_use))
    # list of ((addr, port), server_id) for all replica servers associated with the given key
    replica_buckets = []
    server_hashes = []

    if (server_dict is not None):
        for server_hash, value in server_dict.items():
            server_hashes.append(server_hash)
            replica_buckets.append(value)

    # print ("Server Hashes: {}".format(server_hashes))

    last_dict_elem = None
    server_hashes_in_order = server_hashes
    server_hashes_in_order.sort()
    # print ("Server Hash Ordered List : {}".format(server_hashes_in_order))
    server_hashes_length = len(server_hashes_in_order)
    if (server_hashes_length != 0):
        last_server_hash = server_hashes_in_order[server_hashes_length-1]
        last_dict_elem = server_dict[last_server_hash]

    global bucket_count
    bucket_count = len(replica_buckets)
    has_gtr_hash = False

    # print ("Server Dict : {}".format(server_dict))
    if (server_dict is not None) and (bucket_count != replica_count):
        for server_hash, value in server_dict.items():
            # print ("Server Hash : {}".format(server_hash))
            # print ("Key Hash : {}".format(key_hash))
            # print ("Bucket Count : {}".format(bucket_count))
            # print ("Replica Count : {}".format(replica_count))
            if (server_hash >= key_hash) and (bucket_count < replica_count):
                print ("Found a suitable replica bucket...")
                replica_buckets.append(value)
                bucket_count += 1 
                has_gtr_hash = True
                # print ("Value : {}".format(value))
                # print ("Last Dict Elem : {}".format(last_dict_elem))
                if (value == last_dict_elem) and (bucket_count < replica_count):
                    replica_buckets = add_consecutive_buckets(bucket_count, replica_count, server_hashes_in_order, server_dict, replica_buckets)

        if (has_gtr_hash == False) and (replica_count != 0):
            print ("Couldn't find a suitable replica bucket; wrapping around and using first replica buckets...")
            replica_buckets = add_consecutive_buckets(bucket_count, replica_count, server_hashes_in_order, server_dict, replica_buckets)
    return replica_buckets