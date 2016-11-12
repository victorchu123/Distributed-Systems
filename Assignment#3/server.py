#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3
import socket, server_rpc, sys, common_functions, uuid, argparse

class Server:

    def __init__(self):
        self.src_port = 38000
        args = self.parse_cmd_arguments()
        self.view_leader_ip = args.viewleader
        self.unique_id = uuid.uuid4()
        self.bucket = {}
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

    # Purpose & Behavior: Starts accepting client connections and deals with receiving/responding to messages.
    # Input: Newly created object, and socket that is bound to port within the given range.
    # Output: None
    def accept_and_handle_messages(self, bound_socket, src_port, view_leader_ip):
        # Accept connections forever
        while True:
            try:
                sock, (addr, accepted_port) = bound_socket.accept() # Returns the socket, address and port of the connection
                if (accepted_port is not None): # checks if there is an accepted_port
                    print ("Accepting connection from host " + addr)
                    # receives decoded message length and message from client; if can't throw's an error
                    try: 
                        recvd_msg = common_functions.recv_msg(sock)
                    except ConnectionResetError:
                        print("Connection dropped.")
                    except AttributeError:
                        print ("Cannot decode message.")

                    response = self.process_msg_from_client(recvd_msg)
                    # sends encoded message length and message to client; if can't throw's an error
                    try: 
                        common_functions.send_msg(sock, response)
                    except: 
                        print ("Can't send over whole message.")
                        sock.close()
            except socket.timeout:
                try:
                    print ('Sending heartbeat msg to viewleader...')
                    sock = common_functions.create_connection('localhost', 39000, 39010, 1, False)
                    
                    try:
                        common_functions.send_msg(sock, {'cmd': 'heartbeat', 'args': [str(self.unique_id), src_port, self.view_leader_ip]})
                    except: 
                        print ("Can't send over whole message.")
                        sock.close()

                    try: 
                        recvd_msg = common_functions.recv_msg(sock)
                    except ConnectionResetError:
                        print("Connection dropped.")
                    except AttributeError:
                        print ("Cannot decode message.")

                    print ('Receiving response...')
                    if (recvd_msg is not None):
                        print (str(recvd_msg))
                    sock.close()
                except Exception as e:
                    print ('Heartbeat rejected, will try again in 10 seconds...')
                continue

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
            response = self.unique_id
        elif (function_from_cmd == "get_key"):
            key = recvd_msg["key"]
            try:
                response = self.bucket[key]
            except LookupError:
                response = False
        elif (function_from_cmd == "rebalance"):
            
        else:
            print ("Rejecting RPC request because function is unknown.")

        return response

    def start(self):
        bound_socket, src_port = common_functions.start_listening(self.src_port, 38010, 10)
        self.accept_and_handle_messages(bound_socket, src_port, self.view_leader_ip)
        sock.close() # closes connection with server

if __name__ == '__main__':
    server = Server()