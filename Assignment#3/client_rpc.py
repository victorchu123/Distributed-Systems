import client, common_functions, socket

def get_replica_buckets(viewleader_sock, args_dict):
    common_functions.send_msg(viewleader_sock, args_dict, True)
    # list of (server_hash, (addr, port)) for all replica servers associated with the given key
    replica_buckets = common_functions.recv_msg(viewleader_sock, True)
    return replica_buckets

def get_viewleader_info(viewleader_sock):
    args_dict = {'cmd': 'query_servers'}
    common_functions.send_msg(viewleader_sock, args_dict, True)
    viewleader_response = common_functions.recv_msg(viewleader_sock, True)
    epoch = viewleader_response['Current epoch']
    active_servers = viewleader_response['Active servers']
    return (active_servers, epoch)

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
            server_sock = common_functions.create_connection(addr, port, port, 5, False)
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
    if (rpc_command == 'request_vote'):
        return {'cmd': 'commit'}
    if (response_key is not None):
        result = "No key found in any of the replica servers."
        response_key =  {'status': 'fail', 'result': result}
        return response_key

def distributed_commit(replicas, dest_host, dest_port_low, dest_port_high, timeout):
    viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, 1, True)
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    viewleader_sock.close()

    votes_received = 0
    votes_expected = len(active_servers)
    vote_request = {'cmd': 'request_vote'}
    response = broadcast(replicas, vote_request, epoch, timeout)
    vote = response['cmd']

    # sending global abort
    if (vote == 'abort'):
        print ("Commit failed. Aborting...")
        return False
    # sending global commit
    else:
        print ("Commit succeeded.")
        return True

def setr(key, value, dest_host, dest_port_low, dest_port_high, timeout):
    viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    viewleader_sock.close()

    viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key, 'val': value})
    print ("Replicas : {}".format(replica_buckets))
    viewleader_sock.close()
    length_of_bucket = len(replica_buckets)

    if (length_of_bucket == 0):
        return "Cannot store value because no servers are available."
    else:
        if (distributed_commit(replica_buckets, dest_host, dest_port_low, dest_port_high, timeout)):
            broadcast(replica_buckets, {'cmd': 'setr', 'key': key, 'val': value}, epoch, timeout)
            return "Stored values in replica servers."
        else:
            return "Cannot store value because one of the servers aborted."

def getr(key, dest_host, dest_port_low, dest_port_high, timeout):
    viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True) 
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    viewleader_sock.close()

    viewleader_sock = common_functions.create_connection(dest_host, dest_port_low, dest_port_high, timeout, True)
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key})
    viewleader_sock.close()

    response = broadcast(replica_buckets, {'cmd': 'getr', 'key': key}, epoch, timeout)
    return response
