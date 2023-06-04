#!/bin/bash

# spack load pdiplugin-pycall@1.6.0 pdiplugin-mpi@1.6.0;

MAIN_DIR=$PWD

GR='\033[0;32m'
BL='\033[0;34m'
NC='\033[0m' # No Color

# CHECKING SOFTWARE
echo -n -e "${BL}PDI"   
echo -e "${GR} `which pdirun`${NC}"
echo -n -e "${BL}MPI"   
echo -e "${GR} `which mpirun`${NC}"
echo -n -e "${BL}PYTHON"
echo -e "${GR} `which python`${NC}"
echo -n -e "${BL}RAY"   
echo -e "${GR} `which ray`${NC}"
echo -e "Running in $MAIN_DIR\n"

# COMPILING
(CC=gcc CXX=g++ pdirun cmake .) > /dev/null 2>&1
pdirun make -B simulation

# MPI VALUES
PARALLELISM1=8 # MPI nodes axis x
PARALLELISM2=8 # MPI nodes axis y
MPI_PER_NODE=16 # MPI processes per simulation node

# DATASIZE
DATASIZE1=$((4000*$PARALLELISM1)) # Number of elements axis x
DATASIZE2=$((4000*$PARALLELISM2)) # Number of elements axis y

# STEPS
GENERATION=250 # Number of iterations on the simulation

# ANALYTICS HARDWARE
WORKER_NODES=$(($PARALLELISM1*$PARALLELISM2/16)) # DEISA uses (MPI_PROCESSES/4) worker nodes  with 48 threads each one
CPUS_PER_WORKER=32 # 24 # Parallelism on each worker

# AUXILIAR VALUES
SIMUNODES=$(($PARALLELISM2 * $PARALLELISM1 / $MPI_PER_NODE)) # NUMBER OF SIMULATION NODES
NNODES=$(($WORKER_NODES + $SIMUNODES + 1)) # WORKERS + HEAD + SIMULATION (CLIENT WILL BE WITHIN THE HEAD NODE)
NPROC=$(($PARALLELISM2 * $PARALLELISM1 + $NNODES + 1)) # NUMBER OF DEPLOYED TASKS (MPI + ALL RAY INSTANCES + CLIENT)

# MANAGING FILES
date=$(date +%Y-%m-%d_%X)
OUTPUT=outputs/$date
`which python` prescript.py $DATASIZE1 $DATASIZE2 $PARALLELISM1 $PARALLELISM2 $GENERATION $WORKER_NODES $MPI_PER_NODE $CPUS_PER_WORKER $WORKER_THREADING # Create config.yml
mkdir -p $OUTPUT
mkdir logs 2>/dev/null
touch logs/jobs.log
cp *.yml client.py reisa.py simulation Script.sh $OUTPUT

# RUNNING
cd $OUTPUT
echo $1 > comment.txt
echo -e "Executing $(sbatch --parsable -N $NNODES --partition cpu_short --ntasks=$NPROC Script.sh $SIMUNODES $MPI_PER_NODE $CPUS_PER_WORKER) in $OUTPUT" >> $MAIN_DIR/logs/jobs.log
cd $MAIN_DIR