#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3
import socket, server_rpc, sys, common_functions, uuid, argparse, time, threading, DHT

keys_in_replicas = []

class Server:

    def __init__(self):
        self.src_port = 38000
        args = self.parse_cmd_arguments()
        self.view_leader_ip = args.viewleader
        self.unique_id = uuid.UUID(str(uuid.uuid4())).hex
        self.bucket = {}
        self.last_heartbeat_time = time.time()
        self.epoch = 1
        self.in_commit_phase = []
        self.lock = threading.RLock()
        self.start()
        
    # Purpose & Behavior: Uses argparse to process command line arguments into functions 
    # and their respective inputs. 
    # Input: None
    # Output: namespace of command line arguments
    def parse_cmd_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--viewleader', default='localhost')
        args = parser.parse_args()
        return args

    def send_and_recv_heartbeat(self, src_port):
        # print ('Sending heartbeat msg to viewleader...')
        sock = common_functions.create_connection(self.view_leader_ip, 39000, 39010, 1, False)
        common_functions.send_msg(sock, {'cmd': 'heartbeat', 'args': [str(self.unique_id), src_port]}, False)
        recvd_msg = common_functions.recv_msg(sock, False)
        sock.close()

        if (recvd_msg is not None):
            status = recvd_msg[0]

        sock = common_functions.create_connection(self.view_leader_ip, 39000, 39010, 1, False)
        common_functions.send_msg(sock, {'cmd': 'update_view'}, False)
        curr_epoch = common_functions.recv_msg(sock, False)['Current Epoch']

        # print ("Updating our epoch to {}...".format(curr_epoch))
        self.epoch = curr_epoch
        sock.close()

    # Purpose & Behavior: Starts accepting client connections and deals with receiving/responding to messages.
    # Input: Newly created object, and socket that is bound to port within the given range.
    # Output: None
    def accept_and_handle_messages(self, bound_socket, src_port):
        # Accept connections forever
        while True:
            # sends an heartbeat after 10 seconds, if socket doesn't timeout
            if (time.time() - self.last_heartbeat_time >= 10.0):
                try:
                    self.last_heartbeat_time = time.time()
                    self.send_and_recv_heartbeat(src_port)
                except Exception as e:
                    print ('Heartbeat rejected, will try again in 10 seconds...')
            try:
                sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
                if (accepted_port is not None): # checks if there is an accepted_port
                    print ("Accepting connection from host " + addr)
                    recvd_msg = common_functions.recv_msg(sock, False)
                    response = self.process_msg_from_client(recvd_msg)
                    common_functions.send_msg(sock, response, False)
                    print ("Finished sending message ({}) from server to dest...".format(response))

                    if (time.time() - self.last_heartbeat_time >= 10.0):
                        print ("Sending RPC Message and a RPC heartbeat...")
                        try:
                            self.last_heartbeat_time = time.time()
                            self.send_and_recv_heartbeat(src_port)
                        except Exception as e:
                            print ('RPC Heartbeat rejected...')
            except socket.timeout:
                if (time.time() - self.last_heartbeat_time >= 10.0):
                    try:
                        self.last_heartbeat_time = time.time()
                        self.send_and_recv_heartbeat(src_port)
                    except Exception as e:
                        print ('Heartbeat rejected, will try again in 10 seconds...')
                continue

    def vote(self, epoch, server_id):
        # print ("Comparing viewleader epoch ({}) to our epoch ({})...".format(epoch, self.epoch))
        # print ("Comparing viewleader server id ({}) to our server id ({})...".format(server_id, self.unique_id))
        if (epoch == self.epoch) and (server_id == self.unique_id):
            return 'commit'
        else:
            return 'abort'

    # Purpose & Behavior: Processes commands from the received message and calls upon the 
    # appropriate functions in order to generate a response to the client.
    # Input: Newly created object, and received message in the form of a decoded dictionary {'cmd': str, 'id': int}.
    # Output: Response to the client and will be sent to the client.
    def process_msg_from_client(self, recvd_msg):
        function_from_cmd = recvd_msg["cmd"] # takes function arguments from received dict

        try:
            unique_id = recvd_msg["id"] # takes unique_id from received dict
        except LookupError:
            unique_id = None

        # checks if function is print; if so, then take the text from the received dict
        if (function_from_cmd == "print"):
            text = recvd_msg["text"] # print's argument
            # text length will always be > 0; if text length == 1, 
            # then make text into string rather than a list.
            if (len(text) == 1):
                text = text[0]

            print ("Printing " + str(text))
            response = {'status': 'success','result': text, 'id': unique_id}
        elif (function_from_cmd == "set"):
            server_rpc.set(recvd_msg["key"], recvd_msg["val"])
            response = {'status': 'success', 'id': unique_id}
        elif (function_from_cmd == "get"):
            result = server_rpc.get(recvd_msg["key"])
            if (result is None):
                response = {'status': 'fail', 'result': result, 'id': unique_id}
            else:
                response = {'status': 'success', 'result': result, 'id': unique_id}
        elif (function_from_cmd == "query_all_keys"):
            result = server_rpc.query_all_keys()
            if (result is None):
                response = {'status': 'fail', 'result': result, 'id': unique_id}
            else:
                response = {'status': 'success', 'result': result, 'id': unique_id}
        elif (function_from_cmd == "get_id"):
            # print ("Returning service_id to viewleader...".format(self.unique_id))
            response = str(self.unique_id)
        elif (function_from_cmd == "getr"):
            with self.lock:
                key = recvd_msg["key"]
                try:
                    response = {'status': 'success', 'result': self.bucket[key], 'id': unique_id}
                except LookupError:
                    response = {'status': 'fail', 'result': '', 'id': unique_id}
        elif (function_from_cmd == "setr"):
            with self.lock:
                key = recvd_msg["key"]
                value = recvd_msg["val"]
                try: 
                    self.bucket[key] = value
                    print ("Stored {}:{} in this replica.".format(key, value))
                    response = {'status': 'success', 'id': unique_id}
                except LookupError:
                    response = {'status': 'fail', 'id': unique_id}
        elif (function_from_cmd == "request_vote"):
            key = recvd_msg["key"]
            if (key not in self.in_commit_phase): 
                self.in_commit_phase.append(key)
                # print ("Added key to in_commit_phase: {}".format(self.in_commit_phase))
                viewleader_epoch = recvd_msg["epoch"]
                server_id = uuid.UUID(recvd_msg["server_id"]).hex
                response = self.vote(viewleader_epoch, server_id)
            else:
                print ("Aborting because there is a pending commit...")
                response = 'abort'
            print ("Sending vote back to client...")
        elif (function_from_cmd == "remove_commit"):
            key = recvd_msg["key"]
            # print ("Keys in in_commit_phase: {}".format(self.in_commit_phase))
            # print ("Key: {}".format(key))
            try:
                self.in_commit_phase.remove(key)
            except ValueError:
                print ("Key is not currently being committed.")
            response = {'status': 'success', 'id': unique_id}
        elif (function_from_cmd == "get_data"):
            key = recvd_msg["key"]
            try: 
                response = (key, self.bucket[key])
            except LookupError as e:
                response = None
                print ("Couldn't find the key...")
        elif (function_from_cmd == "rebalance"):
            epoch_op = recvd_msg['op']
            new_view = recvd_msg['new_view']
            old_view = recvd_msg['old_view']

            thread = threading.Thread(target = self.rebalance, args = (new_view, old_view, epoch_op))
            thread.start()
            response = None
        else:
            print ("Rejecting RPC request because function is unknown.")
        return response

    def rebalance(self, new_view, old_view, epoch_op):
        key_to_delete = ''

        for key, value in self.bucket.items():
            old_replicas = DHT.bucket_allocator(key, old_view)
            new_replicas = DHT.bucket_allocator(key, new_view)

            for ((addr, port), server_id) in new_replicas:
                sock = common_functions.create_connection(addr, port, port, 1, False)
                common_functions.send_msg(sock, {'cmd': 'get_data', 'key': key}, False)
                recvd_msg = common_functions.recv_msg(sock, False)
                if (recvd_msg is not None):
                    key_value_replica = recvd_msg
                sock.close()

            key, value = key_value_replica

            with self.lock: 
                if (key not in self.bucket):
                    try:
                        self.bucket[key] = value
                    except LookupError as e:
                        print ("Couldn't set the key since there was no such key...")
                    print ("Adding {}:{} to current replica...".format(new_key, new_value))
                else:
                    if (epoch_op == 'add'):
                        if (old_view is not None):
                            for ((addr, port), server_id) in old_view:
                                if (self.unique_id == server_id) and (((addr, port), server_id) not in new_view):
                                    print ("Deleting {}:{} on old replica...".format(key, value))
                                    key_to_delete = key
        with self.lock:
            try:
                del self.bucket[key_to_delete]
            except LookupError:
                print ("Couldn't delete the key since there was no such key...")

        # with lock:
        #     for bucket in buckets_in_replicas:
        #         for new_key, new_value in bucket.items():
        #             if (new_key not in self.bucket):
        #                 self.bucket[new_key] = new_value
        #                 print ("Adding {}:{} to current replica...".format(new_key, new_value))
        #             if (epoch_op == 'add'):
        #                 if (old_view is not None):
        #                     for ((addr, port), server_id) in old_view:
        #                         if (self.unique_id == server_id) and (((addr, port), server_id) not in view):
        #                             print ("Deleting {}:{} on old replica...".format(key, value))
        #                             del self.bucket[new_key]



    def start(self):
        bound_socket, src_port = common_functions.start_listening(self.src_port, 38010, 10)
        self.accept_and_handle_messages(bound_socket, src_port)
        sock.close() # closes connection with server


if __name__ == '__main__':
    server = Server()