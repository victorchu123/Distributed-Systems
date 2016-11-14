import time, socket, common_functions, view_leader, hashlib
from collections import deque

heartbeats = {}
view = []
locks_held = {}
# dict of (server_hash: ((addr, port), server_id)) for all replica servers
server_ordered_dict = OrderedDict()
replica_count = 0
HASH_MAX = 0

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
def heartbeat(new_id, port, addr, sock, epoch):
    # tuple that we set the corresponding server addr:port to if the heartbeat is accepted
    heartbeats_value = (time.time(), 'working', new_id)

    accept_tuple = ("Heartbeat was accepted.", epoch)
    reject_tuple = ("Heartbeat was rejected.", epoch)

    if ((addr, port) in heartbeats):
        last_timestamp, status, current_id = heartbeats[(addr, port)]
        if (new_id == current_id):      
            if (status == 'working'): 
                print ("Accepting heartbeat from host: " + addr + ":" + str(port))
                common_functions.send_msg(sock, accept_tuple, False)
                heartbeats[(addr, port)] = heartbeats_value
            else:
                print ("Rejecting heartbeat from host: " + addr + ":" + str(port) + " because server failed.")
                common_functions.send_msg(sock, reject_tuple, False)
        else: 
            print ("Accepting heartbeat from host: " + addr + ":" + str(port))
            common_functions.send_msg(sock, accept_tuple, False)
            heartbeats[(addr, port)] = heartbeats_value
    else:
        print ("Accepting heartbeat from host: " + addr + ":" + str(port))
        common_functions.send_msg(sock, accept_tuple, False)
        heartbeats[(addr, port)] = heartbeats_value

def hash_key(d):
    sha1 = hashlib.sha1(d)
    return int(sha1.hexdigest(), 16) % HASH_MAX

def update_DHT():
    addr_port_tuple_lst = []

    if (len(view) >= 3):
        replica_count = 3
    else:
        replica_count = len(view)

    for ((addr, port), server_id) in view:
        addr_port_tuple_lst.append(((addr, port), server_id))

    # checks if dict is non-empty
    if (server_ordered_dict):
        # removes inactive servers from DHT and keeps track of servers in dict
        server_hashes_to_remove = []
        servers_in_dict = []

        for server_hash, value in server_ordered_dict.items():
            if (value not in addr_port_tuple_lst):
                server_hashes_to_remove.append(server_hash)
            servers_in_dict.append(value) 

        for server_hash in server_hashes_to_remove:
            server_ordered_dict.remove(server_hash)
        
    # adds active servers that are not already in DHT, to DHT with new hashes
    for ((addr, port), server_id) in addr_port_tuple_lst:
        if (((addr, port), server_id) not in servers_in_dict): 
            server_sock = create_connection(addr, port, port, None, True) 
            send_msg(server_sock, {'cmd': 'get_id'}, False) 
            server_id = recv_msg(server_sock, False) # unique server id
            server_sock.close()
            server_hash = hash_key(server_id)
            server_ordered_dict[str(server_hash)] = ((addr, port), server_id)

    HASH_MAX = len(server_ordered_dict)

def bucket_allocator(key, value):
    update_DHT() #update DHT
    key_hash = hash_key(key)

    # list of ((addr, port), server_id) for all replica servers associated with the given key
    replica_buckets = []
    bucket_count = 0

    last_dict_elem = server_ordered_dict.items()[len(server_ordered_dict - 1)]

    for server_hash, value in server_ordered_dict.items():
        if (server_hash >= key_hash) and (bucket_count < replica_count):
            replica_buckets.append(value)
            bucket_count += 1
            if ((server_hash, value) == last_dict_elem) and (bucket_count < replica_count):
                if (replica_count == 2):
                    first_dict_elem = server_ordered_dict.items()[0]
                    replica_buckets.append(first_dict_elem[0])
                    bucket_count += 1
                elif (replica_count == 1):
                    first_dict_elem = server_ordered_dict.items()[0]
                    second_dict_elem = server_ordered_dict.items()[1]
                    replica_buckets.append(first_dict_elem[0])
                    bucket_count += 1
                    replica_buckets.append(second_dict_elem[0])
                    bucket_count += 1
    return replica_buckets







