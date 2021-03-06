#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3
import socket, server_rpc, sys, common_functions, uuid, argparse

class Server:

    def __init__(self):
        self.src_port = 38000
        args = self.parse_cmd_arguments()
        self.view_leader_ip = args.viewleader
        self.unique_id = uuid.uuid4()
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

                    response_dict = self.process_msg_from_client(recvd_msg)
                    # sends encoded message length and message to client; if can't throw's an error
                    try: 
                        common_functions.send_msg(sock, response_dict)
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
    # Input: Newly created object, and received message in the form of a decoded dictionary.
    # Output: Dictionary that is the response to the client and will be sent to the client.
    def process_msg_from_client(self, recvd_msg):
        function_from_cmd = recvd_msg["cmd"] # takes function arguments from received dict
        unique_id = recvd_msg["id"] # takes unique_id from received dict
        # checks if function is print; if so, then take the text from the received dict
        if (function_from_cmd == "print"):
            text = recvd_msg["text"] # print's argument
            # text length will always be > 0; if text length == 1, 
            # then make text into string rather than a list.
            if (len(text) == 1):
                text = text[0]

            print ("Printing " + str(text))
            response_dict = {'status': 'success','result': text, 'id': unique_id}
        elif (function_from_cmd == "set"):
            server_rpc.set(recvd_msg["key"], recvd_msg["val"])
            response_dict = {'status': 'success', 'id': unique_id}
        elif (function_from_cmd == "get"):
            result = server_rpc.get(recvd_msg["key"])
            if (result is None):
                response_dict = {'status': 'fail', 'result': result, 'id': unique_id}
            else:
                response_dict = {'status': 'success', 'result': result, 'id': unique_id}
        elif (function_from_cmd == "query_all_keys"):
            result = server_rpc.query_all_keys()
            if (result is None):
                response_dict = {'status': 'fail', 'result': result, 'id': unique_id}
            else:
                response_dict = {'status': 'success', 'result': result, 'id': unique_id}
        else:
            print ("Rejecting RPC request because function is unknown.")

        return response_dict

    def start(self):
        bound_socket, src_port = common_functions.start_listening(self.src_port, 38010, 10)
        self.accept_and_handle_messages(bound_socket, src_port, self.view_leader_ip)
        sock.close() # closes connection with server

if __name__ == '__main__':
    server = Server()