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
	-All features work except for rebalancing. I understood how to rebalance and created a design for it, but I was not able to implement it. I started programming some of rebalancing (which I commented out -- begins at update_view function in view_leader.py), but I didn't understand threads enough to get it to work. However, I will include my design choices in this readme. 

Additional thoughts:
	-Very interesting assignment and it was very challenging. I wish I had a bit more time to complete the assignment.

Design considerations:
	-Bucket allocator algorithm:
		It roughly distributed the keys among my buckets because it hashes each key and finds the smallest server hash value that is still greater or equal to it. Afterwards, it takes the consecutive buckets (number which depends on how many servers are in the view; either 0, 1, or 2), which may wrap around and take the first few buckets in the DHT. Since the hash function gives different values for each key and each server, it is roughly distributed. Moreover, for

