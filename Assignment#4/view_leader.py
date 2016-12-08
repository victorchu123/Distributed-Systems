#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3

import time, server, common_functions, sys, socket, viewleader_rpc, argparse

class ViewLeader():

    def __init__(self):
        self.port = 39000
        self.hostname = socket.gethostname()
        self.args = self.parse_cmd_arguments()
        self.view_leader_list = self.sort_viewleaders(self.args.viewleader.split(","))
        self.leader = self.view_leader_list[len(self.view_leader_list)-1]
        self.log = []
        global last_seen_proposal_num
        last_seen_proposal_num = 0
        self.start()

    # Purpose & Behavior: Uses argparse to process command line arguments into functions 
    # and their respective inputs. 
    # Input: None
    # Output: namespace of command line arguments
    def parse_cmd_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--viewleader', default = common_functions.default_viewleader_ports(3, 39000, 39010))
        args = parser.parse_args()
        return args

    def sort_viewleaders(self, viewleaders):
        viewleader_tuples = []
        for viewleader in viewleaders:
            viewleader_tuples.append((viewleader.split(":")[0], viewleader.split(":")[1]))
        viewleader_tuples.sort()
        return viewleader_tuples

    def start(self):
        sock, src_port = common_functions.start_listening(self.port, 39010, 1) # tries to listen from port 39000-39010 with 1 sec timeout
        self.port = src_port

        if ((self.hostname, str(self.port)) not in self.view_leader_list):
            # print ((self.hostname, self.port))
            # print(self.view_leader_list)
            print ("Viewleader's endpoint is not in viewleader list.")
            sock.close()
            sys.exit()
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
                    self.leader = (self.hostname, self.port)
                    recvd_msg = common_functions.recv_msg(sock, False) # receives message from client/server
                    self.process_msg(recvd_msg, addr, sock)
            except socket.timeout:
                continue
            finally:
                self.update_view()

    # Purpose & Behavior: Processes commands from the received message and calls upon the 
    # appropriate functions in order to generate a response to the client.
    # Input: Received object (dictionary), client/server's source ip address, sock at which viewleader is connected to the source
    # Output: None
    def process_msg(self, recvd_msg, addr, sock):
        function_from_cmd = recvd_msg["cmd"] # takes function arguments from received dict

        if (function_from_cmd == 'query_servers'):
            common_functions.send_msg(sock, viewleader_rpc.query_servers(self.log), False)
        elif (function_from_cmd == 'heartbeat'):
            new_id = recvd_msg["args"][0]
            src_addr = recvd_msg["args"][1]
            src_port = recvd_msg["args"][2] # src port
            timestamp = time.time()
            args = [new_id, src_addr, src_port, timestamp]
            if (self.run_consensus_alg(sock, function_from_cmd, args)):
                self.log.append({'cmd': 'heartbeat', 'id': new_id, 'addr': src_addr, 'port': src_port, 'timestamp': timestamp}.copy())
                viewleader_rpc.heartbeat(new_id, src_port, src_addr, sock, timestamp)
                self.update_view()
                curr_epoch = viewleader_rpc.query_servers(self.log)['Current epoch']
                common_functions.send_msg(sock, {'status': 'ok', 'Current Epoch': curr_epoch}, False)
            else:
                curr_epoch = viewleader_rpc.query_servers(self.log)['Current epoch']
                common_functions.send_msg(sock, {'status': 'not ok', 'Current Epoch': curr_epoch}, False)
        elif (function_from_cmd == 'lock_get'):
            lock_name = recvd_msg["lock_name"]
            requester_id = recvd_msg["requester_id"]
            args = [lock_name, requester_id]
            print ("Running consensus algorithm...")
            if (self.run_consensus_alg(sock, function_from_cmd, args)):    
                self.log.append({'cmd': 'lock_get', 'lock': lock_name, 'requester': requester_id}.copy())
                is_got = viewleader_rpc.lock_get(lock_name, requester_id)

                if (is_got):
                    common_functions.send_msg(sock, {'status': 'granted'}, False)
                else:
                    common_functions.send_msg(sock, {'status': 'retry'}, False)
                    print ("Sending retry message to client.")
            else:
                common_functions.send_msg(sock, {'status': 'not ok'}, False)
        elif (function_from_cmd == 'lock_release'):
            lock_name = recvd_msg["lock_name"]
            requester_id = recvd_msg["requester_id"]
            args = [lock_name, requester_id]
            if (self.run_consensus_alg(sock, function_from_cmd, args)):
                self.log.append({'cmd': 'lock_release', 'lock': lock_name, 'requester': requester_id}.copy())
                is_released = viewleader_rpc.lock_release(lock_name, requester_id)

                if (is_released):
                    common_functions.send_msg(sock, {'status': 'ok'}, False)
                else:
                    common_functions.send_msg(sock, {'status': 'not ok'}, False)
            else: 
                common_functions.send_msg(sock, {'status': 'not ok'}, False)
        elif (function_from_cmd == 'rebalance'):
            msg = recvd_msg['msg']
            print (msg)
        elif (function_from_cmd == 'prepare'):
            proposal_num = recvd_msg['proposal_num']
            length_of_log = len(self.log)

            # promise message Phase 1
            global last_seen_proposal_num
            if (last_seen_proposal_num < proposal_num):
                last_seen_proposal_num = proposal_num

            if (proposal_num == length_of_log):
                common_functions.send_msg(sock, {'status': 'ok', 'addr': self.hostname, 'port': self.port}, False)
            elif (proposal_num < length_of_log):
                logs_for_leader = self.log[proposal_num:length_of_log]
                common_functions.send_msg(sock, {'status': 'ok', 'logs_leader_is_missing': logs_for_leader, 'addr': self.hostname, 'port': self.port}, False)
            else:
                common_functions.send_msg(sock, {'status': 'ok', 'num_logs_replica_needs': proposal_num - length_of_log, 'addr': self.hostname, 'port': self.port}, False)
        
        elif (function_from_cmd == 'accept'):
            # print ("Proposal: {}".format(recvd_msg))
            new_proposal_num = recvd_msg['new_proposal_num']
            new_cmd = recvd_msg['new_cmd']
            args = recvd_msg['args']

            try:
                logs_for_replica = recvd_msg['logs_replica_needs']
                if (last_seen_proposal_num <= new_proposal_num):
                    # print ("Log before update: {}".format(self.log))
                    print ("Replaying logs on this replica...")
                    self.replay(logs_for_replica)
                    if (len(self.log) != 0):
                        print ("Updated log: {}".format(self.log))
                        pass
            except Exception:
                print ("No logs missing.")

            if (new_cmd == 'heartbeat'):
                new_id = args[0]
                src_addr = args[1]
                src_port = args[2]
                timestamp = args[3]
            else:
                lock_name = args[0]
                requester_id = args[1]

            if (new_cmd == 'heartbeat'):
                self.log.append({'cmd': 'heartbeat', 'id': new_id, 'addr': src_addr, 'port': src_port, 'timestamp': timestamp}.copy())
                viewleader_rpc.heartbeat(new_id, src_port, src_addr, sock, timestamp)
                self.update_view()
            elif (new_cmd == 'lock_get'):
                self.log.append({'cmd': 'lock_get', 'lock': lock_name, 'requester': requester_id}.copy())
                is_got = viewleader_rpc.lock_get(lock_name, requester_id)

                if (is_got):
                    common_functions.send_msg(sock, {'status': 'granted'}, False)
                else:
                    common_functions.send_msg(sock, {'status': 'retry'}, False)
                    print ("Sending retry message to client.")
            elif (new_cmd == 'lock_release'):
                self.log.append({'cmd': 'lock_release', 'lock': lock_name, 'requester': requester_id}.copy())
                is_released = viewleader_rpc.lock_release(lock_name, requester_id)

                if (is_released):
                    common_functions.send_msg(sock, {'status': 'ok'}, False)
                else:
                    common_functions.send_msg(sock, {'status': 'not ok'}, False)
            # print ("Updated log: {}".format(self.log))
        else:
            print ("Rejecting RPC request because function is unknown.")

    def broadcast(self, msg, replicas):
        responses = []
        leader_hostname = self.leader[0]
        leader_port = str(self.leader[1])

        for replica in replicas:
            addr, port = replica
            # print ((addr, port), (leader_hostname, leader_port))
            if ((addr, port) != (leader_hostname, leader_port)):
                sock = common_functions.create_connection(addr, port, port, 1, False)
                if (sock):
                    common_functions.send_msg(sock, msg, False)
                    recvd_msg = common_functions.recv_msg(sock, False)   
                    if (recvd_msg):
                        responses.append(recvd_msg)
                    sock.close()
        return responses

    def replay(self, logs_leader_is_missing):
        for logs in logs_leader_is_missing:
            cmd = logs['cmd']
            if (cmd == 'lock_get'):
                lock = logs['lock']
                requester = logs['requester']
                is_accepted = viewleader_rpc.lock_get(lock, requester)
                if (is_accepted):
                    print ("Appending cmd to log...")
                    self.log.append({'cmd': 'lock_get', 'lock': lock, 'requester': requester}.copy())
            elif (cmd == 'lock_release'):
                lock = logs['lock']
                requester = logs['requester']
                is_accepted = viewleader_rpc.lock_get(lock, requester)
                if (is_accepted):
                    print ("Appending cmd to log...")
                    self.log.append({'cmd': 'lock_release', 'lock': lock, 'requester': requester}.copy())
            elif (cmd == 'heartbeat'):
                server_id = logs['id']
                addr = logs['addr']
                port = logs['port']
                timestamp = logs['timestamp']
                # print ('Replaying heartbeat... with args: {}'.format([server_id, addr, port, timestamp]))
                is_accepted = viewleader_rpc.heartbeat(server_id, port, addr, None, timestamp)
                if (is_accepted):
                    print ("Appending cmd to log...")
                    self.log.append({'cmd': 'heartbeat', 'id': server_id, 'addr': addr, 'port': port, 'timestamp': timestamp}.copy())

    def find_max(self, logs_missing):
        if (len(logs_missing) == 0):
            return None
        elif (len(logs_missing) == 1):
            return len(logs_missing[0]) 
        else:
            return max(len(logs_missing[0]), self.find_max(logs_missing[1:]))
    
    def find_max_log(self, logs_missing):
        max_len = self.find_max(logs_missing)
        for logs in logs_missing:
            if len(logs) == max_len:
                return logs

    def has_quorum(self, responses):
        # print ("Responses: {}".format(responses))
        num_replicas_agreed = 1 # initialize with the leader's self, which obviously agrees with itself
        logs_leader_is_missing = []

        for response in responses:
            try:
                if (response['status'] == 'ok'):
                    num_replicas_agreed += 1 # adds 1 for each positive response from a replica
                # leader needs to catch up
                if (response['logs_leader_is_missing']):
                    logs_leader_is_missing.append(response['logs_leader_is_missing'])
            except Exception:
                # print ("No logs missing from current replica.")
                pass

        log_to_replay = self.find_max_log(logs_leader_is_missing)
        if (log_to_replay):
            self.replay(log_to_replay)
            if (len(self.log)!= 0):
                # print ("Updated log: {}".format(self.log))
                pass

        # print ("num_replicas_agreed: {}, Quorum requirement: {}".format(num_replicas_agreed, round(len(self.view_leader_list)/2)))
        if (num_replicas_agreed >= round(len(self.view_leader_list)/2)):
            return True
        else:
            print ("Quorum has not been met, aborting command.")
            return False # quorum of replicas hasn't been reached

    def run_consensus_alg(self, sock, cmd, args):
        proposal_num = len(self.log) # proposal number is equivalent to length of log
        msg = {'cmd': 'prepare', 'proposal_num': proposal_num} # prepare message; Phase 1
        print ("Broadcasting prepare message to replicas...")
        responses = self.broadcast(msg, self.view_leader_list)

        if (self.has_quorum(responses)):
            for response in responses:
                status = None
                num_logs_replica_needs = None
                logs_leader_is_missing = None

                try:
                    replica_addr = response['addr']
                    replica_port = response['port']
                    status = response['status']
                    if (status == 'ok'):
                        status = 'accept' # accept message; Phase 2
                    else:
                        status = 'reject'
                except Exception:
                    # print("Invalid response.")
                    continue
                try:
                    num_logs_replica_needs = response['num_logs_replica_needs']
                except Exception:
                    # print ("No logs need to be sent to this replica.")
                    pass
                try: 
                    logs_leader_is_missing = response['logs_leader_is_missing']
                except Exception:
                    # print ("No logs need to be received from this replica.")
                    pass

                if (num_logs_replica_needs):
                    print ("num_logs_replica_needs: {}".format(num_logs_replica_needs))
                    logs_to_replay = self.log[len(self.log) - num_logs_replica_needs:]
                    print ("logs_to_replay: {}".format(len(logs_to_replay)))
                    msg = {'cmd' : status, 'logs_replica_needs' : logs_to_replay,
                     'new_proposal_num': len(self.log), 'new_cmd': cmd, 'args': args} 
                elif (logs_leader_is_missing):
                    msg = {'cmd' : status, 'new_proposal_num': len(self.log), 'new_cmd': cmd, 'args': args} 
                elif (status):
                    msg = {'cmd' : status, 'new_proposal_num': len(self.log), 'new_cmd': cmd, 'args': args} 
                
                if (status == 'accept'):
                    sock = common_functions.create_connection(replica_addr, replica_port, replica_port, 1, False)
                    common_functions.send_msg(sock, msg, False)
                if (sock):
                    sock.close()
            return True
        else:
            return False


    # Purpose & Behavior: Updates the view 
    # Input: None
    # Output: None
    def update_view(self):
        failed_servers = []
        current_heartbeats = []
        # dict of all received heartbeats in the form of {'(server addr, server port): (last_timestamp, status, current_id)'}
        heartbeats = viewleader_rpc.heartbeats
        view = viewleader_rpc.view # dict of all active servers

        old_view = view.copy()

        # adds server to a list if they haven't responded in more than 30 seconds
        for (addr,port), (last_timestamp, status, server_id) in heartbeats.items():
            if (time.time() - last_timestamp > 30.0) and (status == 'working'):
                print ("It has been more than 30 seconds since last heartbeat, marking server as failed.")
                failed_servers.append((addr,port))

        # marks crashed/failed servers as failed
        for server in failed_servers:
            last_timestamp, status, current_id = heartbeats[server]
            heartbeats[server] = (last_timestamp, 'failed', current_id) 

        # print ("Heartbeats: {}".format(heartbeats))   

        # adds working servers to view and removes failing servers
        for (addr,port), (new_timestamp, status, server_id) in heartbeats.items():
            if (status == 'working'):
                try: 
                    last_timestamp = view[(addr, port, server_id)]
                    if (last_timestamp < new_timestamp):
                        view[(addr, port, server_id)] = new_timestamp
                except Exception:
                    view[(addr, port, server_id)] = new_timestamp
                # send rebalance RPC request to server
                # self.rebalance(old_view, view, 'add')
            elif (status == 'failed'):
                try:
                    del view[(addr, port, server_id)]
                except Exception:
                    pass
                # send rebalance RPC request to server
                # self.rebalance(old_view, view, 'remove')

        view_servers_to_remove = []
        for (view_addr, view_port, view_server_id), view_last_timestamp in view.items():
            for (heart_addr, heart_port), (heart_last_timestamp, status, heart_server_id) in heartbeats.items():
                if ((view_addr, view_port) == (heart_addr, heart_port)) and (heart_server_id != view_server_id):
                    view_servers_to_remove.append((view_addr, view_port, view_server_id))

        # print ("view_servers_to_remove: {}".format(view_servers_to_remove))  

        for server in view_servers_to_remove:
            try:
                del view[server]
            except Exception:
                pass
            print ("Removing servers that have been replaced...")
            # self.rebalance(old_view, view, 'remove')

    # Purpose & Behavior: Broadcasts rebalance RPC to all servers in new_view
    # Input: server's unique id, server's src port, server's src ip, and the socket
    # connects server to viewleader 
    # Output: None
    def rebalance(self, old_view, new_view, epoch_op):
        for ((addr, port), server_id) in new_view:
            server_sock = common_functions.create_connection(addr, port, port, None, False) 
            common_functions.send_msg(server_sock, {'cmd': 'rebalance', 'old_view': old_view, 'new_view': new_view, 'op': epoch_op}, False)
            server_sock.close() 

if __name__ == '__main__':
    view_leader = ViewLeader()