import hashlib

HASH_MAX = 1000

def hash_key(d):
	sha1 = hashlib.sha1(d)
	return int(sha1.hexdigest(), 16) % HASH_MAX

key = "".encode('utf-8')
print(hash_key(key))