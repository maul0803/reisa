To launch the program ensure you have loaded **pycall and mpi plugins from PDI** (v1.6.0) and dependencies, you have installed **ray** (v2.3.0), the python module netifaces and run the following script:

 `./Launcher.sh`

 This command will compile simulation.c with PDI and MPI, then a batch job will start ray in every necessary node and run the previous simulation.

 The simulation will use the simulation.yml in order set up ray, run the analytics code and gather the results. The file simulation.yaml is the core of the program.

 The idea is just to make it necessary to modify the code inside the reisa.py file.