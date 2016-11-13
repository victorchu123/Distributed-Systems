import client, common_functions

def get_replica_buckets(viewleader_sock, args_dict):
    common_functions.send_msg(viewleader_sock, args_dict, True)
    # list of (server_hash, (addr, port)) for all replica servers associated with the given key
    replica_buckets = common_functions.recv_msg(viewleader_sock, True)
    return replica_buckets

def get_current_view(viewleader_sock):
    args_dict = {'cmd': 'get_view'}
    common_functions.send_msg(viewleader_sock, args_dict, True)
    view = common_functions.recv_msg(viewleader_sock, True)
    return view

def distributed_commit():
    viewleader_sock = common_functions.create_connection(client.dest_host, client.dest_port_low, client.dest_port_high, None, True)
    view = get_current_view(viewleader_sock)
    viewleader_sock.close()

    vote_request = {'cmd': 'vote_request'}
    for (addr, port) in view:

        common_functions.send_msg(vote_request,)

def setr(key, value):
    viewleader_sock = common_functions.create_connection(client.dest_host, client.dest_port_low, client.dest_port_high, None, True)
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key, 'val': value})
    viewleader_sock.close()
    # store and write distributed commit 
    # for (ip, port) in replica_buckets:

def getr(key):
    viewleader_sock = common_functions.create_connection(client.dest_host, client.dest_port_low, client.dest_port_high, None, True) 
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key})
    viewleader_sock.close()

    for (server_hash, (addr, port)) in replica_buckets:
        server_sock = common_functions.create_connection(addr, port, port, None, True) 
        send_msg(server_sock, {'cmd': 'get_key', 'key': key}, False) 
        response_key = recv_msg(server_sock, False) # desired value associated with the given key from DHT
        viewleader_sock.close()
        
        if (response_key != False):
            return {'status': 'success', 'result': response_key}

    if (response_key == False):
        result = "No key found in any of the replica servers."
        response =  {'status': 'fail', 'result': result}
    return response
