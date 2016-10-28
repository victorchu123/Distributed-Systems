Name: Victor Chu

Instructions:
	-Navigate to directory with all .py files with 'cd' command in Terminal.

	SERVER
	------
	-Run the command 'python3 server.py' to start up the server, which listens on a open port for the client, and sends heartbeats to the viewleader.
	-Run the command 'python3 server.py -h' for usage details (in order to specify the viewleader IP Address).

	CLIENT
	------
	-Run the command 'python3 client.py' to start up the client. 
	-Run the command 'python3 client.py -h' for usage details (in order to specify the viewleader IP Address and call RPC functions).

	VIEWLEADER
	----------
	-Run the command 'python3 view_leader.py' to start up the viewleader, which starts listening for the server/client.

State:
	-Fully working, no known bugs.

Additional thoughts:
	-Very interesting assignment and it was challenging.