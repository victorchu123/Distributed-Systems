memo = {}

def fib(n):
	if (n <= 2): 
		return 1
	else:
		if (n in memo):
			return memo[n]
		else:
			f_sum = fib(n-1) + f(n-2)
			memo[n] = f_sum
			return f_sum