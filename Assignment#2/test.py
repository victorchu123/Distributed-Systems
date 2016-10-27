from collections import deque

waiter_queue = deque(['Victor'])

def test(requester):
	if (waiter_queue.popleft() == requester):
		waiter_queue.popleft()
		print(waiter_queue)
		return True

test('Victor')