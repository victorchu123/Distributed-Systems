#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3

import time, server, common_functions, sys, socket, viewleader_rpc

epoch = 0

class ViewLeader():

    def __init__(self):
        self.src_port = 39000
        self.start()

    def start(self):
        sock, src_port = common_functions.start_listening(self.src_port, 39010, 1) # tries to listen from port 39000-39010 with 1 sec timeout
        self.accept_msg(sock)
        sock.close()

    # Purpose & Behavior: Tries to accept message from the client/server source socket and updates the view
    # Input: socket at which viewleader is connected with the source
    # Output: None
    def accept_msg(self, bound_socket):
        # Accept connections forever
        while True:
            try:
                sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
                if (accepted_port is not None): # checks if there is an accepted_port
                    recvd_msg = common_functions.recv_msg(sock, False) # receives message from client/server
                    self.process_msg(recvd_msg, addr, sock)
                    self.update_view() # updates view
            except socket.timeout:
                # updates view when socket timesout
                self.update_view()
                continue

    # Purpose & Behavior: Processes commands from the received message and calls upon the 
    # appropriate functions in order to generate a response to the client.
    # Input: Received object (dictionary), client/server's source ip address, sock at which viewleader is connected to the source
    # Output: None
    def process_msg(self, recvd_msg, addr, sock):
        function_from_cmd = recvd_msg["cmd"] # takes function arguments from received dict

        if (function_from_cmd == 'query_servers'):
            global epoch
            common_functions.send_msg(sock, viewleader_rpc.query_servers(epoch), False)
        elif (function_from_cmd == 'heartbeat'):
            new_id = recvd_msg["args"][0]
            port = recvd_msg["args"][1] # src port
            viewleader_rpc.heartbeat(new_id, port, addr, sock, epoch)
        elif (function_from_cmd == 'lock_get'):
            lock_name = recvd_msg["lock_name"]
            requester_id = recvd_msg["requester_id"]

            if (viewleader_rpc.lock_get(lock_name, requester_id) == True):
                common_functions.send_msg(sock, "{'status': 'granted'}", False)
            else:
                common_functions.send_msg(sock, "{'status': 'retry'}", False)
                print ("Sending retry message to client.")
        elif (function_from_cmd == 'lock_release'):
            lock_name = recvd_msg["lock_name"]
            requester_id = recvd_msg["requester_id"]
            if (viewleader_rpc.lock_release(lock_name, requester_id) == True):
                common_functions.send_msg(sock, "{'status': 'ok'}", False)
            else:
                common_functions.send_msg(sock, "{'status': 'not ok'}", False)
        elif (function_from_cmd == 'bucket_allocator'):
            key = recvd_msg["key"]
            if (value is not None):
                value = recvd_msg["val"]
            replica_buckets = viewleader_rpc.bucket_allocator(key, value)
            common_functions.send_msg(sock, replica_buckets, False)
        else:
            print ("Rejecting RPC request because function is unknown.")

    # Purpose & Behavior: Updates the view 
    # Input: None
    # Output: None
    def update_view(self):
        failed_servers = []
        # dict of all received heartbeats in the form of {'(server addr, server port): (last_timestamp, status, current_id)'}
        heartbeats = viewleader_rpc.heartbeats
        view = viewleader_rpc.view # list of all active servers
        global epoch

        # adds server to a list if they haven't responded in more than 30 seconds
        for key, value in heartbeats.items():
            if (time.time() - value[0] > 30.0) and (value[1] == 'working'):
                print ("It has been more than 30 seconds since last heartbeat, marking server as failed.")
                failed_servers.append(key)

        # marks crashed/failed servers as failed
        for server in failed_servers:
            last_timestamp, status, current_id = heartbeats[server]
            heartbeats[server] = (last_timestamp, 'failed', current_id)    

        # adds working servers to view and removes failing servers (also updates epoch when either of these actions happen)
        for key, value in heartbeats.items():
            if (value[1] == 'working') and (key not in view):
                view.append(key)
                epoch = epoch + 1
                # send rebalance RPC request to server
                # rebalance(view)
                
            elif (value[1] == 'failed') and (key in view):
                view.remove(key)
                epoch = epoch + 1
                # send rebalance RPC request to server
                # rebalance(view)

    def rebalance(view):
        for (addr, port) in view:
            server_sock = create_connection(addr, port, port, None, True) 
            send_msg(server_sock, {'cmd': 'rebalance', 'view': view}, False) 

if __name__ == '__main__':
    view_leader = ViewLeader()