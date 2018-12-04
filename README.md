# CS220_GUROBI

The project tends to build an ILP-based Placement-and-Routing system for continuous flow microfluidics. Please download the whole directory, and run 'python columba.py'. You can generate a routing netlist result named 'columba.json' out of the input file 'input.json'. 

To obatin diffenrent optimized netlist, you should modify values in the 'params.txt'. From top to bottom, each value will be assigned to variables, which are alpha, beta, gamma, and kappa, inside 'columba.py' in sequence. The sample output netlist file 'sample.json' is the result of alpha = 1, beta = 1, gamma = 1,  and kappa = 1.

NOTICE: The constructed environment contains python 2.7.10 and gurobi 8.

## Known Bugs
1. Although the channels are routed, they will still have overlaps with components and other channels. 
2. Sometimes the ILP Optimizer will take very long time to obtain the result (alpha = 1, beta = 1, gamma = 1, kappa = 1). Not sure whether the reason is that my constrains added are not precise.

## LINK
[GitHub](https://github.com/Sadort/CS220_GUROBI)

