import time, socket, common_functions
from collections import deque

heartbeats = {} # dict of all received heartbeats in the form of {'(server addr, server port): (last_timestamp, status, current_id)'}
view = {} # dict of all active servers in the form of '(addr, port, server_id)' : last_timestamp
locks_held = {} # lock table in the form of 'lock_name': (waiter_queue, owner)


# Purpose & Behavior: Returns current view and epoch
# Input: current log from viewleader
# Output: dictionary of list of active servers and the current epoch
def query_servers(log):
    # print ("Log: {}".format(log))
    # print ("View: {}".format(view))
    # print ("Heartbeats: {}".format(heartbeats))
    info = []
    epoch = 0
    for (addr, port, server_id), last_timestamp in view.items():
        info.append((addr + ':' + str(port), server_id, last_timestamp))

    heartbeat_dict = {}

    for entry in log:
        cmd = entry['cmd']
        if cmd == 'heartbeat':
            server_id = entry['id']
            timestamp = entry['timestamp']
            try:
                last_timestamp = heartbeat_dict[server_id]
                if (last_timestamp < timestamp):
                    heartbeat_dict[server_id] = timestamp
            except:
                heartbeat_dict[server_id] = timestamp

    for server_id, timestamp in heartbeat_dict.items():
        if (time.time() - timestamp > 30.0):
            epoch += 1
        epoch += 1

    return ({'Active servers': info, 'Current epoch': epoch})

# Purpose & Behavior: Attempts to obtain the lock for the requester
# Input: lock name and requester id
# Output: True (lock is granted) or False (lock is denied and will retry)
def lock_get(lock, requester):
    # checks if lock is held
    if (lock not in locks_held):
        waiter_queue = deque([])
        # adds lock to dictionary and sets requester as the current holder
        locks_held[lock] = (waiter_queue, requester)
        print ("Lock is not held. {} now holds lock {}.".format(requester, lock))
        return True
    else: 
        held_msg = "Lock is held."
        waiter_queue, current_holder = locks_held[lock]
        if (current_holder == requester):
            print (held_msg + " Current requester holds the lock.")
            return True
        else: 
            if (requester not in locks_held[lock][0]):
                # adds requester to waiting queue since the lock is already held
                print (held_msg + " Adding requester to {}'s".format(lock) + " waiter queue.")
                locks_held[lock][0].append(requester)
                return False
            else:
                print (held_msg + " Request is already in {}'s".format(lock) + " waiter queue.")
                return False

# Purpose & Behavior: Attempts to release the lock for the requester
# Input: lock name and requester id
# Output: True (lock is successfully released) or False (lock is either not held by the 
# requester or not held at all)
def lock_release(lock, requester):
    # checks if lock is held already
    if (lock in locks_held):
        waiter_queue, current_holder = locks_held[lock]
        if (len(waiter_queue) == 0) and (requester == current_holder):
            del locks_held[lock]
            print ("Lock has no waiter in queue, so lock is being released and unheld.")
            return True
        elif (len(waiter_queue) > 0) and (requester == current_holder): 
            # takes off the first waiter in the queue and sets him as the current holder
            new_holder = waiter_queue.popleft()
            locks_held[lock] = (waiter_queue, new_holder)
            print ("Lock released. Passing lock onto next waiter.")
            return True
        elif (len(waiter_queue) > 0) and (requester in waiter_queue):
            waiter_queue.remove(requester)
            print ("Requester removed from the waiter queue.")
            return True
        else:
            print ("Requester doesn't hold the lock and isn't waiting for it.")
            return False
    else:
        print ("Lock is not held!")
        return False

# Purpose & Behavior: Attempts to send a heartbeat to the viewleader.
# Input: server's unique id, server's src port, server's src ip, and the socket
# connects server to viewleader, timestamp of heartbeat
# Output: None
def heartbeat(new_id, port, addr, sock, timestamp):
    # tuple that we set the corresponding server addr:port to if the heartbeat is accepted
    heartbeats_value = (timestamp, 'working', new_id)

    if ((addr, port) in heartbeats):
        last_timestamp, status, current_id = heartbeats[(addr, port)]
        if (last_timestamp < timestamp):
            if (new_id == current_id):      
                if (status == 'working'): 
                    print ("Accepting heartbeat from host: " + addr + ":" + str(port))
                    heartbeats[(addr, port)] = heartbeats_value
                    return True
                else:
                    print ("Rejecting heartbeat from host: " + addr + ":" + str(port) + " because server failed.")
                    return False
            else:
                print ("Accepting heartbeat from host: " + addr + ":" + str(port))
                heartbeats[(addr, port)] = heartbeats_value
                return True
    else:
        print ("Accepting heartbeat from host: " + addr + ":" + str(port))
        heartbeats[(addr, port)] = heartbeats_value
        return True




