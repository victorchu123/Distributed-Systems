# Distributed File System
*Features: Remote Procedure Call, Centralized Lock Server, Heartbeat Failure Detection, Rebalancing Distributed Hash Table, and Viewleader Data Redundancy*
## Instructions:
	1) Navigate to directory with all .py files with 'cd' command in Terminal.
	
	**VIEWLEADER** (holds list of active servers, list of active locks (view), and processes RPC function calls from Client as well as heartbeat failure check from Server)
	----------
	-Run the command 'python3 view_leader.py' to start up the viewleader, which starts listening for the server/client.
	-Run the command 'python3 view_leader.py -h' for usage details (in order to specify the viewleader IP Address).

	**SERVER** (for receiving and processing RPC function calls from Client)
	------
	-Run the command 'python3 server.py' to start up the server, which listens on a open port for the client, and sends heartbeats to the viewleader.
	-Run the command 'python3 server.py -h' for usage details (in order to specify the viewleader IP Address).

	**CLIENT** (able to call RPC functions from Server as well as from Viewleader)
	------
	-Run the command 'python3 client.py' to start up the client. 
	-Run the command 'python3 client.py -h' for usage details (in order to specify the viewleader IP Address and call RPC functions).

## State:

All features work except for a case where the server temporarily crashes, is rejected by my viewleaders, and then I start up another viewleader, which becomes the leader, and then I crash the same server again, and reopen it. The server has the same addr/port, but has a different server id, and for some reason my viewleaders still reject heartbeats from a server with this addr/port. I believe there is something wrong with my update_view and/or heartbeat function for this case.

