defmodule Counter do 
	
	// actor
	def counter_loop(val) do
		receive do
			{:INCREMENT} -> counter_loop(val+1) // tail-recursion; so memory is fine even when it's being called infinitely
			{:GET, pid} -> send pid, {:GOTTEN, val}
							counter_loop(val)
		end
		// IO.puts "hello" // last line is returned; this would end the recursion and the actor would die
	end

	// actor
	def start_counter_loop() do
		spawn fn -> counter_loop(0) end
	end

end
