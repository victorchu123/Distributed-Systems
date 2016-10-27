#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3

import time, server, common_functions, sys, socket, viewleader_rpc


class ViewLeader():

    def __init__(self):
        self.src_port = 39000
        self.start()

    def start(self):
        sock = common_functions.start_listening(self.src_port, 39010, 5)
        self.accept_msg(sock)
        sock.close()

    # Purpose & Behavior:
    # Input: 
    # Output:
    def accept_msg(self, bound_socket):
        # Accept connections forever
        while True:
            try:
                sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
                if (accepted_port is not None): # checks if there is an accepted_port
                    recvd_msg = common_functions.recv_msg(sock)
                    self.process_msg_from_client(recvd_msg, addr, sock)
                self.update_view()
            except socket.timeout as e:
                self.update_view()
                continue

    # Purpose & Behavior: Processes commands from the received message and calls upon the 
    # appropriate functions in order to generate a response to the client.
    # Input: Newly created object, and received message in the form of a decoded dictionary.
    # Output: Dictionary that is the response to the client and will be sent to the client.
    def process_msg_from_client(self, recvd_msg, addr, sock):
        function_from_cmd = recvd_msg["cmd"] # takes function arguments from received dict

        if (function_from_cmd == 'query_servers'):
            common_functions.send_msg(viewleader_rpc.query_servers())
        elif (function_from_cmd == 'heartbeat'):
            new_id = recvd_msg["args"][0]
            port = recvd_msg["args"][1] # src port
            viewleader_ip = recvd_msg["args"][2]
            heartbeat(new_id, port, viewleader_ip, addr, sock)

        elif (function_from_cmd == 'lock_get'):
            lock_name = recvd_msg["lock_name"]
            requester_id = recvd_msg["requester_id"]

            if (viewleader_rpc.lock_get(lock_name, requester_id) == True):
                common_functions.send_msg(sock, "{'status': 'granted'}")
            else:
                common_functions.send_msg(sock, "{'status': 'retry'}")
                print ("Sending retry message to client.")

        elif (function_from_cmd == 'lock_release'):
            lock_name = recvd_msg["lock_name"]
            requester_id = recvd_msg["requester_id"]
            if (viewleader_rpc.lock_release(lock_name, requester_id) == True):
                common_functions.send_msg(sock, "{'status': 'ok'}")
            else: 
                common_functions.send_msg(sock, "{'status': 'not ok'}")
          
        else:
            print ("Rejecting RPC request because function is unknown.")

    def update_view(self):
        failed_servers = []

        heartbeats = viewleader_rpc.heartbeats
        view = viewleader_rpc.view
        epoch = viewleader_rpc.epoch

        for key, value in heartbeats.items():
            if (time.time() - value[0] > 30) and (value[1] == 'working'):
                print ("It has been more than 30 seconds since last heartbeat, marking server as failed.")
                failed_servers.append(key)

        for server in failed_servers:
            last_timestamp, status, current_id = heartbeats[server]
            heartbeats[server] = (last_timestamp, 'failed', current_id)    

        # print (self.heartbeats)

        for key, value in heartbeats.items():
            if (value[1] == 'working') and (key not in view):
                view.append(key)
                epoch += 1
            elif (value[1] == 'failed') and (key in view):
                view.remove(key)
                epoch += 1

        if (epoch != 0) and (len(view) != 0):
            print (viewleader_rpc.view, epoch)


if __name__ == '__main__':
    view_leader = ViewLeader()