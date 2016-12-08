def find_max(logs_missing):
    if (len(logs_missing) == 0):
        return None
    elif (len(logs_missing) == 1):
        return len(logs_missing[0])	
    else:
        return max(len(logs_missing[0]), find_max(logs_missing[1:]))

logs_missing = [[3,4,5,6], [3,2], [2,2], [1], [3,1,2], [2,2,2,2]]
max_len = find_max(logs_missing)

for logs in logs_missing:
	if len(logs) == max_len:
		print (logs)
