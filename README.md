To launch the program ensure you have loaded **pycall and mpi plugins from PDI** (v1.6.0) and dependencies, you have installed **ray['complete']** and **ray['debug']** (v2.4.0), the python module **netifaces** and run the following script:

 `./Launcher.sh`

 This command will compile simulation.c with PDI and MPI, then a batch job will start Ray in every necessary node and run the previous simulation.

 The simulation will use the simulation.yml in order set up Ray in each MPI process.

 The user just needs to modify client.py file to manage the analytics tasks.

 The execution will generate a timeline-client.json file that you can read with Google Chrome in chrome://tracing to see the execution stream.