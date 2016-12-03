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
	-All features work except for rebalancing. I understood how to rebalance and created a design for it, but I was not able to fully implement it. I tried my best to get rebalancing to work, which does work when I have 3 or less servers open and I add another server in and it will rebalance. Whenever I have three or more servers open, I seem to run into situations where I get timeout and broken pipe errors. Moreover, when I shutdown some servers, I get a loop where it tries to keep connecting to failed servers even though I put exception handling for it (possibly deadlock). 
	- In order to remove rebalancing, comment out lines 113 and 118 in view_leader.py.

Design considerations:
	-Bucket allocator algorithm:
		It roughly distributed the keys among my buckets because it hashes each key and finds the smallest server hash value that is still greater or equal to it. Afterwards, it takes the consecutive buckets (number which depends on how many servers are in the view; either 0, 1, or 2), which may wrap around and take the first few buckets in the DHT. Since the hash function gives different values for each key and each server, it is roughly distributed. 

		Moreover, for the circumstances where my algorithm needs to rebalance are when I add a server that ends up with a hash that is before another server (and right after the hash of the given key) that is a replica. In that case, the keys/values from the old replica will have to go to our server, which becomes the new replica. Another situation where we need to rebalance is when we remove an existing replica with keys/values. These key/values have to be passed on to the next following server, which becomes a replica if it wasn't already.
	-Rebalancing implementation:
		Whenever there is an epoch change, my viewleader sends out a rebalance RPC (with the arguments: old_view, new_view, and epoch_operation) to all servers in the active view, and afterwards, the servers will use the bucket_allocator on each one of their keys (on both old and new views) in order to get all the replicas.If the server is in the new replica, then it will talk to the other servers in the new replica and send/receive data from them through an RPC (get_data), and will update it's own data to be the key/value from the other replica if it doesn't have the key/value already. Also, if the epoch_operation is 'add' then it will replica that was in the old_view but is not in the new_view, then that replica will additionally have the current key/value removed from its bucket.

		My implementation reduces load on the view leader because it doesn't keep any key specific information on there and doesn't have to communicate with each individual server aside from passing them the old_view, new_view, and epoch_operation. By having the servers talk to each other, the viewleader has less load. It minimizes copying of keys/values since it only has new_replicas talking to each other, and only sets new keys/values if it doesn't exist in the replicas' bucket already. 
	-Distributed Commit
		I implemented distributed commit by following the algorithm in the textbook. I used RPCs query_servers, setr, remove_commit, and request_vote. The one main difference between my approach and the book's is that I decided to not collect all the vote, but rather send an abort back to the client as soon as one server votes against the commit. In that way, I do not have to wait for votes from all servers if it is not necessary and I don't have to do a global abort later, since I only use setr (aka go through with the commit) if the distributed commit goes through.
