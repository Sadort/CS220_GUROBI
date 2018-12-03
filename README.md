# CS220_GUROBI

The project tends to build an ILP-based Placement-and-Routing system for continuous flow microfluidics. Please download the whole directory, and run 'python columba.py'. You can generate a routing netlist result named 'data.json'. 

To obatin diffenrent optimized netlist, you should modify values in the 'params.txt'. From top to bottom, each value will be assigned to variables, which are alpha, beta, gamma, and kappa, inside 'columba.py' in sequence. The sample output netlist file 'data.json' is the result of alpha = 1, beta = 1, gamma = 1,  and kappa = 1.

NOTICE: The constructed environment contains python 2.7.10 and gurobi 8.

## LINK
[GitHub]
(https://github.com/Sadort/CS220_GUROBI)
