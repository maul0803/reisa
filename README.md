## RAISA: Ray-enabled in situ analytics

RAISA is a data analytics model for in-situ and in-transit workflows based Ray, a Python framework providing a distributed execution model.

RAISA exposes a distributed task-based paradigm for in-situ o in-transit analytics coupled to MPI numerical simulations at scale.

Authors: Xico Fernández Lozano, Bruno Raffin, Julien Bigot and Emilio J. Padrón

## Deployment

To launch the program ensure you have loaded **pycall and mpi plugins from PDI** (v1.6.0) and dependencies, you have installed **ray['complete']** and **ray['debug']** (v2.4.0), the python module **netifaces** and run the following script:

 `./Launcher.sh`

 This command will compile simulation.c with PDI and MPI, then a batch job will start Ray in every necessary node and run the previous simulation.

 The simulation will use the simulation.yml in order set up Ray in each MPI process.

 The user just needs to modify client.py file to manage the analytics tasks.

 The execution will generate a timeline-client.json file that you can read with Google Chrome in chrome://tracing to see the execution stream.
