#Distributed System with Remote Procedure Call, Centralized Lock Server, and Heartbeat Failure Detection
##Instructions:
	1) Navigate to directory with all .py files with 'cd' command in Terminal.
	
	2) Start up Viewleader, Server, and then Client. 
	
	**VIEWLEADER** (holds list of active servers, list of active locks (view), and processes RPC function calls from Client as well as heartbeat failure check from Server)
	----------
	-Run the command 'python3 view_leader.py' to start up the viewleader, which starts listening for the server/client.


	**SERVER** (for receiving and processing RPC function calls from Client)
	------
	-Run the command 'python3 server.py' to start up the server, which listens on a open port for the client, and sends heartbeats to the viewleader.
	-Run the command 'python3 server.py -h' for usage details (in order to specify the viewleader IP Address).
	

	**CLIENT** (able to call RPC functions from Server as well as from Viewleader)
	------
	-Run the command 'python3 client.py' to start up the client. 
	-Run the command 'python3 client.py -h' for usage details (in order to specify the viewleader IP Address and call RPC functions).

