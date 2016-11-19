import socket, json, struct, sys

# Purpose & Behavior: Encodes a message and then sends it to the defined socket.
# Input: Newly created object, and socket where TCP connection is created and the object that we
# want to send over.
# Output: None
def send_msg(sock, object_to_send, exit):
    # sends encoded message length and message to destination; if can't throw's an error
    try:
        # print ("Sending RPC msg to destination: {}...".format(object_to_send))
        # serializing object into a JSON formatted stream and then encoded 
        # into a unicode string.
        send_msg_encoded = json.dumps(object_to_send).encode()
        send_msg_length = len(send_msg_encoded) # send message size 
        send_msg_length_encoded = struct.pack("!i", send_msg_length) # encodes an int as a 32-bit binary value; big-endian

        sock.sendall(send_msg_length_encoded) # sends encoded "message length"
        sock.sendall(send_msg_encoded) # sends encoded message
    except Exception as e: 
        print ("Failed send over whole message ({}): ".format(object_to_send), e)
        if (sock is not None):
            sock.close()
        if (exit):
            sys.exit()

# Purpose & Behavior: Receives a message from the sender socket and decodes it. 
# Input: Newly created object, and socket where TCP connection is created.
# Output: received message that is a decoded object
def recv_msg(sock, exit):
    # receives decoded message length and message from source; if can't throw's an error
    try:
        # Receive at most msg_length bytes
        # Returns value received
        length_of_length = 4 # length of the (length of the received message)
        recvd_msg_length_encoded = sock.recv(length_of_length, socket.MSG_WAITALL) # reads the message's (from sending socket) length
        recvd_msg_length, = struct.unpack("!i", recvd_msg_length_encoded) # decodes the 32-bit binary value as an int; big-endian
        recvd_msg = sock.recv(recvd_msg_length, socket.MSG_WAITALL)# reads the message
        # print ("Received RPC msg from source: {}...".format(recvd_msg))
        if (len(recvd_msg) == 0):
            # recv gives 0 result if the connection has been closed
            print("Connection terminated.") 
        elif (len(recvd_msg) != recvd_msg_length):
            print("Incomplete message.") 
        else:
            recvd_msg = json.loads(recvd_msg.decode('utf-8')) # decodes the received message
            return recvd_msg
    except ConnectionResetError:
        print("Connection dropped.")
    except AttributeError:
        print ("Cannot decode message.")
    except Exception as e:
        print ("Couldn't receive message: ", e)
    if (sock is not None):
        sock.close()
    if (exit):
        sys.exit()

# Purpose & Behavior: Starts TCP connection from this source to dest
# Input: destination host, destination port lower bound & upper bound, timeout for socket, and boolean
# indicating whether to exit the system or not.
# Output: Socket where TCP connection is created.
def create_connection(dest_host, dest_port_low, dest_port_max, timeout, exit):
    dest_port = dest_port_low
    while (dest_port <= dest_port_max):
        # print ("Creating connection with destination..")
        # print('Trying to connect to ' + dest_host + ':' + str(dest_port) + '...')
        # Note these calls may throw an exception if it fails
        try:
            sock = socket.create_connection((dest_host, dest_port), timeout) # opens connection with view leader
            break
        except Exception as e:
            if (dest_port < dest_port_max):
                dest_port += 1
            else:
                print ("Cannot find an open port from {}-{}: ".format(dest_port_low, dest_port_max), e)
                if (exit):
                    sys.exit()
                else: 
                    print ("Breaking from loop...")
                    break
    return sock

# Purpose & Behavior: Starts listening on the designated src port for a source host
# Input: source port lower bound & upper bound, timeout for socket
# Output: Tuple of socket that is bound to source port and source port
def start_listening(src_port_low, src_port_max, timeout):
    src_port = src_port_low
    # tries to listen on port range; it will stop if it either finds an open port or gives up
    while (src_port <= src_port_max):
        print ("Trying to listen on "+ str(src_port) + '...')
        # Note these calls may throw an exception if it fails
        try:
            bound_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            bound_socket.bind(('', src_port)) # binds socket to src port
            bound_socket.listen(3) # socket starts listening for client
            bound_socket.settimeout(timeout)
            break
        except Exception as e:
            if (src_port < src_port_max):
                src_port += 1
            else:
                print ("Cannot find an open port from {}-{}: ".format(src_port_low, src_port_max), e)
                sys.exit()
            continue
    return (bound_socket, src_port)

