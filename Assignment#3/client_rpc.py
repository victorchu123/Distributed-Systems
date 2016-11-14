import client, common_functions

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

def broadcast(replicas, object_to_send, epoch):
    for ((addr, port), server_id) in replicas:
        if (object_to_send['cmd'] == 'request_vote'):
            object_to_send['epoch'] = epoch
            object_to_send['server_id'] = server_id
        server_sock = common_functions.create_connection(addr, port, port, None, False)
        common_functions.send_msg(server_sock, object_to_send, False)
        if (object_to_send['cmd'] == 'getr'):
            response_key = recv_msg(server_sock, False) # desired value associated with the given key from DHT
            if (response_key != ''):
                return {'status': 'success', 'result': response_key}
        elif (object_to_send['cmd'] == 'setr'):
            response = recv_msg(server_sock, False)
    if (response_key is not None):
        if (response_key == ''):
            result = "No key found in any of the replica servers."
            response =  {'status': 'fail', 'result': result}
            return response
    server_sock.close()

def distributed_commit(replicas):
    viewleader_sock = common_functions.create_connection(client.dest_host, client.dest_port_low, client.dest_port_high, None, True)
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    viewleader_sock.close()

    votes_received = 0
    votes_expected = len(active_servers)
    abort = False
    vote_request = {'cmd': 'request_vote'}
    broadcast(replicas, votes_request, epoch)

    bound_socket, src_port = common_functions.start_listening(37000, 37010, 10)

    global_abort = {'cmd': 'abort'}
    global_commit = {'cmd': 'commit'}

    while (votes_received < votes_expected) and (abort == False):
        try:
            sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
            if (accepted_port is not None): # checks if there is an accepted_port
                print ("Accepting vote from " + addr)
                recvd_msg = common_functions.recv_msg(sock, False)
                vote = self.process_msg_from_client(recvd_msg)
                if (vote == 'abort'):
                    abort = True
                votes_received += 1
        except socket.timeout:
            abort = True

    if (abort):
        broadcast(replicas, global_abort, epoch)
        print ("Commit failed. Aborting...")
        return False
    else:
        broadcast(replicas, global_commit, epoch)
        print ("Commit succeeded.")
        return True

def setr(key, value):
    viewleader_sock = common_functions.create_connection(client.dest_host, client.dest_port_low, client.dest_port_high, None, True)
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key, 'val': value})
    viewleader_sock.close()
    length_of_bucket = len(replica_buckets)

    if (length_of_bucket == 0):
        return "Cannot store value because no servers are available."
    else:
        if (distributed_commit(replica_buckets)):
            broadcast(replica_buckets, {'cmd': 'setr', 'key': key, 'val': value}, epoch)
            return "Stored values in replica servers."
        else:
            return "Cannot store value because one of the servers aborted."

def getr(key):
    viewleader_sock = common_functions.create_connection(client.dest_host, client.dest_port_low, client.dest_port_high, None, True) 
    replica_buckets = get_replica_buckets(viewleader_sock, {'cmd': 'get_buckets', 'key': key})
    active_servers, epoch = get_viewleader_info(viewleader_sock)
    viewleader_sock.close()
    response = broadcast(replica_buckets, {'cmd': 'getr', 'key': key}, epoch)
    return response
