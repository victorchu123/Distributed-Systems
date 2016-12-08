#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3
import socket, argparse, sys, common_functions, time, client_rpc

class Client:

    def __init__(self): 
        self.start()

    # Purpose & Behavior: Uses argparse to process command line arguments into functions 
    # and their respective inputs. 
    # Input: None
    # Output: namespace of command line arguments
    def parse_cmd_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--server', default='localhost')
        parser.add_argument('--viewleader', default='localhost')

        subparsers = parser.add_subparsers(dest='cmd')

        parser_set = subparsers.add_parser('set')
        parser_set.add_argument('key', type=str)
        parser_set.add_argument('val', type=str)

        parser_get = subparsers.add_parser('get')
        parser_get.add_argument('key', type=str)

        parser_print = subparsers.add_parser('print')
        parser_print.add_argument('text', nargs="*")

        parser_query = subparsers.add_parser('query_all_keys')

        parser_query_servers = subparsers.add_parser('query_servers')

        parser_lock_get = subparsers.add_parser('lock_get')
        parser_lock_get.add_argument('lock_name', type=str)
        parser_lock_get.add_argument('requester_id', type=str)

        parser_lock_release = subparsers.add_parser('lock_release')
        parser_lock_release.add_argument('lock_name', type=str)
        parser_lock_release.add_argument('requester_id', type=str)

        parser_setr = subparsers.add_parser('setr')
        parser_setr.add_argument('key', type=str)
        parser_setr.add_argument('val', type=str)

        parser_getr = subparsers.add_parser('getr')
        parser_getr.add_argument('key', type=str)

        args = parser.parse_args()
        return args
  
    # Purpose & Behavior: Creates a dictionary from the provided namespace; 
    # deletes unnecessary entries and adds unique id entry to the dict.
    # Input: Newly created object, and command line argument namespace (args)
    # Output: Dictionary with relevant entries with keys (unique id, cmd, (key/text/val) depending on cmd)
    def create_dict(self, args):
        args_dict = vars(args) # converts args namespace to a dict
        keys_to_delete = []

        # removes "server" key from dict, 
        # so we only send over the necessary arguments.
        for key, value in args_dict.items():
            if (key == "server") or (key == "viewleader"):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del args_dict[key]

        request_id = 0 # creates a unique id for the RPC
        args_dict["id"] = request_id # adds entry to args_dict with the "id" key

        return args_dict

    def start(self):
        args = self.parse_cmd_arguments()

        # if the optional argument "--server" is used, 
        # then set localhost as this computer's IP. else, return error and exit.
        if (args.server is not None):
            if (args.cmd is None):
                print ("RPC command not provided.")
                sys.exit()

        viewleader_args = ['query_servers', 'lock_get', 'lock_release']

        self.timeout = 1
        # sets destination port ranges and destination hosts based on the RPC functions called
        if (args.cmd in viewleader_args):
            self.dest_host = str(args.viewleader)
            self.dest_port_low = 39000
            self.dest_port_high = 39010
            self.dest_name = 'viewleader'
        elif (args.cmd == 'getr' or args.cmd == 'setr'):
            self.dest_host = str(args.viewleader)
            self.dest_port_low = 39000
            self.dest_port_high = 39010
            self.dest_name = 'viewleader_and_server'
        else:
            self.dest_host = str(args.server)
            self.dest_port_low = 38000
            self.dest_port_high = 38010
            self.dest_name = 'server'

        args_dict = self.create_dict(args)

        stop = False
        sock = None

        if (self.dest_name == 'viewleader_and_server'):
            stop = True
            if (args.cmd == 'getr'):
                print (client_rpc.getr(args.key, self.dest_host, self.dest_port_low, self.dest_port_high, self.timeout))
            else: 
                print (client_rpc.setr(args.key, args.val, self.dest_host, self.dest_port_low, self.dest_port_high, self.timeout))
        while (stop == False):
            sock = common_functions.create_connection(self.dest_host, self.dest_port_low, self.dest_port_high, self.timeout, True)
            # sends encoded message length and message to server/viewleader; if can't throw's an error
            common_functions.send_msg(sock, args_dict, True)
            recvd_msg = common_functions.recv_msg(sock, True)
            if (recvd_msg == "{'status': 'retry'}"):
                print (str(recvd_msg))
                time.sleep(5) # delays for 5 seconds and then tries again
            else: 
                print (str(recvd_msg))
                stop = True  
            
        if (sock is not None):
            sock.close()
        sys.exit()

if __name__ == '__main__':
    client = Client()
