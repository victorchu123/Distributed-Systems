import time, socket, common_functions, view_leader
from collections import deque

heartbeats = {}
view = []
locks_held = {}

# Purpose & Behavior: Returns current view and epoch
# Input: epoch from viewleader
# Output: dictionary of list of active servers and the current epoch
def query_servers(epoch):
    info = []
    for addr, port in view:
        info.append(addr + ':' + str(port))
    return ({'Active servers': str(info), 'Current epoch': str(epoch)})

# Purpose & Behavior: Attempts to obtain the lock for the requester
# Input: lock name and requester id
# Output: True (lock is granted) or False (lock is denied and will retry)
def lock_get(lock, requester):
    # checks if lock is held
    if (lock not in locks_held):
        print ("Lock is not held.")
        waiter_queue = deque([])
        # adds lock to dictionary and sets requester as the current holder
        locks_held[lock] = (waiter_queue, requester)
        print ("{} now holds lock {}.".format(requester, lock))
        return True
    else: 
        print ("Lock is held.")
        waiter_queue, current_holder = locks_held[lock]
        if (current_holder == requester):
            print ("Current requester holds the lock.")
            return True
        else: 
            if (requester not in locks_held[lock][0]):
                # adds requester to waiting queue since the lock is already held
                print ("Adding requester to {}'s".format(lock) + " waiter queue.")
                locks_held[lock][0].append(requester)
                return False
            else:
                print ("Request is already in {}'s".format(lock) + " waiter queue")
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
            print ("Lock released.")
            # takes off the first waiter in the queue and sets him as the current holder
            new_holder = waiter_queue.popleft()
            locks_held[lock] = (waiter_queue, new_holder)
            print ("Passing lock onto next waiter.")
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
# connects server to viewleader 
# Output: None
def heartbeat(new_id, port, addr, sock):
    # tuple that we set the corresponding server addr:port to if the heartbeat is accepted
    heartbeats_value = (time.time(), 'working', new_id)

    if ((addr, port) in heartbeats):
        last_timestamp, status, current_id = heartbeats[(addr, port)]
        if (new_id == current_id):      
            if (status == 'working'): 
                print ("Accepting heartbeat from host: " + addr + ":" + str(port))
                common_functions.send_msg(sock, "Heartbeat was accepted.")
                heartbeats[(addr, port)] = heartbeats_value
            else:
                print ("Rejecting heartbeat from host: " + addr + ":" + str(port) + " because server failed.")
                common_functions.send_msg(sock, "Heartbeat was rejected.")
        else: 
            print ("Accepting heartbeat from host: " + addr + ":" + str(port))
            common_functions.send_msg(sock, "Heartbeat was accepted.")
            heartbeats[(addr, port)] = heartbeats_value
    else:
        print ("Accepting heartbeat from host: " + addr + ":" + str(port))
        common_functions.send_msg(sock, "Heartbeat was accepted.")
        heartbeats[(addr, port)] = heartbeats_value