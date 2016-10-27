import time, socket, common_functions, view_leader
from collections import deque

heartbeats = {}
view = []
locks_held = {}

def query_servers(epoch):
    info = []
    for addr, port in view:
        info.append(addr + ':' + str(port))
    return ({'Active servers': str(info), 'Current epoch': str(epoch)})

# True: Lock is granted
# False: Lock is denied
def lock_get(lock, requester):
    if (lock not in locks_held):
        print ("Lock is unheld.")
        waiter_queue = deque([])
        locks_held[lock] = (waiter_queue, requester)
        print ("{} now holds lock {}.".format(requester, lock))
        return True
    else: 
        print ("Lock is held.")
        waiter_queue, current_holder = locks_held[lock]
        if (current_holder is None) or (current_holder == ''):
            new_holder = waiter_queue.popleft()
            locks_held[lock] = (waiter_queue, new_holder)
            print ("Passing lock onto next waiter.")
            return True
        if (current_holder == requester):
            print ("Current requester holds the lock.")
            return True
        else: 
            if (requester not in locks_held[lock][0]):
                print ("Adding requester to {}'s".format(lock) + " waiter queue.")
                locks_held[lock][0].append(requester)
                return False
            else:
                print ("Request is already in {}'s".format(lock) + " waiter queue")
                return False

def lock_release(lock, requester):
    waiter_queue, current_holder = locks_held[lock]
    if (lock in locks_held):
        if (waiter_queue.count == 0):
            locks_held.remove(lock)
            print ("Lock has no waiter in queue, so lock is being released and unheld.")
            return True
        else: 
            locks_held[lock] = (waiter_queue, '')
            print ("Lock released, clearing out current holder.")
            return True
    else:
        print ("Lock is not held!")
        return False

def heartbeat(new_id, port, viewleader_ip, addr, sock):
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