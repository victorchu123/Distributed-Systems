import client, common_functions, socket

# Purpose & Behavior: Sends a get_buckets RPC to viewleader in order to get the replica buckets.
# Input: viewleader socket, RPC object to send
# Output: replica buckets
def get_replica_buckets(viewleader_sock, args_dict):
    common_functions.send_msg(viewleader_sock, args_dict, True)
    # list of (server_hash, (addr, port)) for all replica servers associated with the given key
    replica_buckets = common_functions.recv_msg(viewleader_sock, True)
    return replica_buckets

# Purpose & Behavior: Sends a query_servers RPC to viewleader.
# Input: viewleader socket
# Output: active servers and epoch tuple
def get_viewleader_info(viewleader_sock):
    args_dict = {'cmd': 'query_servers'}
    common_functions.send_msg(viewleader_sock, args_dict, True)
    viewleader_response = common_functions.recv_msg(viewleader_sock, True)
    epoch = viewleader_response['Current epoch']
    active_servers = viewleader_response['Active servers']
    return (active_servers, epoch)

# Purpose & Behavior: Broadcasts RPC object to all replicas/servers given
# Input: replicas/servers, RPC object, epoch, timeout
# Output: Response
def broadcast(replicas, object_to_send, epoch, timeout):
    response_key = None
    rpc_command = object_to_send['cmd']
    abort = False
    votes = []

    for ((addr, port), server_id) in replicas:
        if (rpc_command == 'request_vote'):
            object_to_send['epoch'] = epoch
            object_to_send['server_id'] = str(server_id)
        try: 
            server_sock = common_functions.create_connection(addr, port, port, timeout, False)
            # print ("Sending {} to replica server {}...".format(object_to_send, (addr, port)))
            common_functions.send_msg(server_sock, object_to_send, False)

            if (rpc_command == 'request_vote'):
                vote = common_functions.recv_msg(server_sock, False)
                print ("Accepting vote from " + addr)
                if (vote == 'abort'):
                    abort = True
                    return {'cmd': 'abort'}
            if (rpc_command == 'getr'):
                response_key = common_functions.recv_msg(server_sock, False) # desired value associated with the given key from DHT
            if (response_key is not None):
                return response_key
            elif (rpc_command == 'setr'):
                response_key = common_functions.recv_msg(server_sock, False)
            server_sock.close()
        except socket.timeout:
            if (rpc_command == 'request_vote'):
                abort = True
                return {'cmd': 'abort'}
        except Exception as e:
            print ("Couldn't connect to current replica server...will continue on remaining replicas: ", e)
            continue 
    if (rpc_command == 'request_vote'):
        return {'cmd': 'commit'}
    if (response_key is not None):
        result = "No key found in any of the replica servers."
        response_key =  {'status': 'fail', 'result': result}
        return response_key

# Purpose & Behavior: Sends a distributed commit to all given replicas and returns a response based on their votes
# Input: replicas, key, destination host, destination port range, timeout
# Output: True/False (commit succeeded or failed)
def distributed_commit(replicas, key, dest_host, dest_port_low, dest_port_high, timeout):
    try:
        viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
        active_servers, epoch = get_viewleader_info(viewleader_sock)
    except Exception as e:
        print ("Couldn't establish a connection with viewleader: ", e)
        
    viewleader_sock.close()

    votes_received = 0
    votes_expected = len(active_servers)
    vote_request = {'cmd': 'request_vote', 'key': key}
    response = broadcast(replicas, vote_request, epoch, 5)
    vote = response['cmd']

    # sending global abort
    if (vote == 'abort'):
        print ("Commit failed. Aborting...")
        return False
    # sending global commit
    else:
        print ("Commit succeeded.")
        return True

# Purpose & Behavior: Tries to set values on suitable replica servers; will set at max 3 replica servers for each key
# Input: key/value to set, destination host ip, destination port ranges, timeout
# Output: Status message
def setr(key, value, dest_host, dest_port_low, dest_port_high, timeout):
    try:
        viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
        active_servers, epoch = get_viewleader_info(viewleader_sock)
    except Exception as e:
        print ("Couldn't establish a connection with viewleader: ", e)
    viewleader_sock.close()

    try:
        viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
        replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key, 'val': value})
        print ("Replicas : {}".format(replica_buckets))
    except Exception as e:
        print ("Couldn't establish a connection with viewleader: ", e)

    viewleader_sock.close()
    length_of_bucket = len(replica_buckets)

    if (length_of_bucket == 0):
        return "Cannot store value because no servers are available."
    else:
        if (distributed_commit(replica_buckets, key, dest_host, dest_port_low, dest_port_high, 3)):
            broadcast(replica_buckets, {'cmd': 'setr', 'key': key, 'val': value, 'id': 0}, epoch, 5)
            broadcast(replica_buckets, {'cmd': 'remove_commit', 'key': key, 'id': 0}, epoch, 5)
            return "Stored values in replica servers."
        else:
            broadcast(replica_buckets, {'cmd': 'remove_commit', 'key': key, 'id': 0}, epoch, 5)
            return "Cannot store value because one of the servers aborted."

# Purpose & Behavior: Tries to get value associated with the given key by contacting replica servers
# Input: key, destination host ip, destination port ranges, timeout
# Output: value associated with the given key
def getr(key, dest_host, dest_port_low, dest_port_high, timeout):
    try: 
        viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True) 
    except Exception as e:
        print ("Couldn't establish a connection with viewleader: ", e)
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    viewleader_sock.close()

    viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key})
    viewleader_sock.close()

    response = broadcast(replica_buckets, {'cmd': 'getr', 'key': key, 'id': 0}, epoch, 5)
    return response
