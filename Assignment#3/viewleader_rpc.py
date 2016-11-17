import time, socket, common_functions, hashlib, uuid
from collections import deque

heartbeats = {}
view = []
locks_held = {}
# dict of (server_hash: ((addr, port), server_id)) for all replica servers
server_dict = {}
replica_count = 0
bucket_count = 0
HASH_MAX = 160

# Purpose & Behavior: Returns current view and epoch
# Input: epoch from viewleader
# Output: dictionary of list of active servers and the current epoch
def query_servers(epoch):
    info = []
    for ((addr, port), server_id) in view:
        info.append((addr + ':' + str(port), server_id))
    return ({'Active servers': info, 'Current epoch': epoch})

# Purpose & Behavior: Attempts to obtain the lock for the requester
# Input: lock name and requester id
# Output: True (lock is granted) or False (lock is denied and will retry)
def lock_get(lock, requester):
    # checks if lock is held
    if (lock not in locks_held):
        print ("Lock is not held.")
        waiter_queue = deque([])
        # adds lock to dictionary and sets requester as the current holder
        locks_held[lock] = (waiter_queue, requester)
        print ("{} now holds lock {}.".format(requester, lock))
        return True
    else: 
        print ("Lock is held.")
        waiter_queue, current_holder = locks_held[lock]
        if (current_holder == requester):
            print ("Current requester holds the lock.")
            return True
        else: 
            if (requester not in locks_held[lock][0]):
                # adds requester to waiting queue since the lock is already held
                print ("Adding requester to {}'s".format(lock) + " waiter queue.")
                locks_held[lock][0].append(requester)
                return False
            else:
                print ("Request is already in {}'s".format(lock) + " waiter queue")
                return False

# Purpose & Behavior: Attempts to release the lock for the requester
# Input: lock name and requester id
# Output: True (lock is successfully released) or False (lock is either not held by the 
# requester or not held at all)
def lock_release(lock, requester):
    # checks if lock is held already
    if (lock in locks_held):
        waiter_queue, current_holder = locks_held[lock]
        if (len(waiter_queue) == 0) and (requester == current_holder):
            del locks_held[lock]
            print ("Lock has no waiter in queue, so lock is being released and unheld.")
            return True
        elif (len(waiter_queue) > 0) and (requester == current_holder): 
            print ("Lock released.")
            # takes off the first waiter in the queue and sets him as the current holder
            new_holder = waiter_queue.popleft()
            locks_held[lock] = (waiter_queue, new_holder)
            print ("Passing lock onto next waiter.")
            return True
        elif (len(waiter_queue) > 0) and (requester in waiter_queue):
            waiter_queue.remove(requester)
            print ("Requester removed from the waiter queue.")
            return True
        else:
            print ("Requester doesn't hold the lock and isn't waiting for it.")
            return False
    else:
        print ("Lock is not held!")
        return False

# Purpose & Behavior: Attempts to send a heartbeat to the viewleader.
# Input: server's unique id, server's src port, server's src ip, and the socket
# connects server to viewleader 
# Output: None
def heartbeat(new_id, port, addr, sock):
    # tuple that we set the corresponding server addr:port to if the heartbeat is accepted
    heartbeats_value = (time.time(), 'working', new_id)

    accept_tuple = ("Heartbeat was accepted.")
    reject_tuple = ("Heartbeat was rejected.")

    if ((addr, port) in heartbeats):
        last_timestamp, status, current_id = heartbeats[(addr, port)]
        if (new_id == current_id):      
            if (status == 'working'): 
                print ("Accepting heartbeat from host: " + addr + ":" + str(port))
                heartbeats[(addr, port)] = heartbeats_value
                common_functions.send_msg(sock, accept_tuple, False)
            else:
                print ("Rejecting heartbeat from host: " + addr + ":" + str(port) + " because server failed.")
                common_functions.send_msg(sock, reject_tuple, False)
        else:
            print ("Accepting heartbeat from host: " + addr + ":" + str(port))
            heartbeats[(addr, port)] = heartbeats_value
            common_functions.send_msg(sock, accept_tuple, False)
    else:
        print ("Accepting heartbeat from host: " + addr + ":" + str(port))
        heartbeats[(addr, port)] = heartbeats_value
        common_functions.send_msg(sock, accept_tuple, False)

def hash_key(d):
    d_encoded = d.encode('utf-8')
    sha1 = hashlib.sha1(d_encoded)
    # print ("HASH_MAX : {}".format(HASH_MAX))
    try:
        return int(sha1.hexdigest(), 16) % HASH_MAX
    except ZeroDivisionError as e:
        print ("Cannot mod by 0: ", e)

def is_val_in_server_dict(val):
    for key, value in server_dict.items():
        if (server_dict[key] == val):
            return True
    return False

def update_DHT():
    global replica_count
    if (len(view) >= 3):
        replica_count = 3
    else:
        replica_count = len(view)

    print ("View: {}".format(view))

    servers_in_dict = []
    # checks if dict is non-empty
    if (len(servers_in_dict) != 0):
        print ("Removing inactive servers...")
        # removes inactive servers from DHT and keeps track of servers in dict
        server_hashes_to_remove = []

        for server_hash, value in server_dict.items():
            if (value not in view):
                server_hashes_to_remove.append(server_hash)
            servers_in_dict.append(value) 

        for server_hash in server_hashes_to_remove:
            del server_dict[server_hash]
        
    # adds active servers from view that are not already in DHT, to DHT with new hashes
    for ((addr, port), server_id) in view:
        if (is_val_in_server_dict(((addr, port), server_id)) == False): 
            # server_sock = common_functions.create_connection(addr, port, port, 2, True) 
            # common_functions.send_msg(server_sock, {'cmd': 'get_id'}, False) 
            # response = common_functions.recv_msg(server_sock, False)
            # print ("Response: {}".format(response))
            # server_id = uuid.UUID(response).hex # unique server id
            # print ("Server ID: {}".format(server_id))
            # server_sock.close()
            server_hash = hash_key(server_id)
            # print ("Server Hash: {}".format(server_hash))
            server_dict[server_hash] = ((addr, port), server_id)

    print ("Server Dict: {}".format(server_dict))

def bucket_allocator(key):
    update_DHT() #update DHT
    key_hash = hash_key(key)

    # list of ((addr, port), server_id) for all replica servers associated with the given key
    replica_buckets = []
    server_hashes = []

    if (server_dict is not None):
        for server_hash, value in server_dict.items():
            server_hashes.append(server_hash)

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
    has_gtr_hash = False

    if (server_dict is not None):
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
                print ("Value : {}".format(value))
                print ("Last Dict Elem : {}".format(last_dict_elem))
                if (value == last_dict_elem) and (bucket_count < replica_count):
                    if (replica_count == 2):
                        first_server_hash = server_hashes_in_order[0]
                        first_dict_elem = server_dict[first_server_hash]
                        replica_buckets.append(first_dict_elem)
                        bucket_count += 1
                    elif (replica_count == 3):
                        first_server_hash = server_hashes_in_order[0]
                        first_dict_elem = server_dict[first_server_hash]
                        second_server_hash = server_hashes_in_order[1]
                        second_dict_elem = server_dict[second_server_hash]
                        replica_buckets.append(first_dict_elem)
                        bucket_count += 1
                        replica_buckets.append(second_dict_elem)
                        bucket_count += 1

        if (has_gtr_hash == False) and (replica_count != 0):
            print ("Couldn't find a suitable replica bucket; wrapping around and using first replica buckets...")
            if (replica_count == 1):
                first_server_hash = server_hashes_in_order[0]
                first_dict_elem = server_dict[first_server_hash]
                replica_buckets.append(first_dict_elem)
                bucket_count += 1
            elif (replica_count == 2):
                first_server_hash = server_hashes_in_order[0]
                first_dict_elem = server_dict[first_server_hash]
                second_server_hash = server_hashes_in_order[1]
                second_dict_elem = server_dict[second_server_hash]
                replica_buckets.append(first_dict_elem)
                bucket_count += 1
                replica_buckets.append(second_dict_elem)
                bucket_count += 1
            elif (replica_count == 3):
                first_server_hash = server_hashes_in_order[0]
                first_dict_elem = server_dict[first_server_hash]
                second_server_hash = server_hashes_in_order[1]
                second_dict_elem = server_dict[second_server_hash]
                third_server_hash = server_hashes_in_order[2]
                third_dict_elem = server_dict[third_server_hash]
                replica_buckets.append(first_dict_elem)
                bucket_count += 1
                replica_buckets.append(second_dict_elem)
                bucket_count += 1
                replica_buckets.append(third_dict_elem)
                bucket_count += 1

    return replica_buckets







