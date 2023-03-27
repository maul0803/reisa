#!/bin/bash

# spack load pdiplugin-pycall@1.6.0 pdiplugin-mpi@1.6.0;

# BASE VALUES
PARALLELISM1=4
PARALLELISM2=4
MPI_PER_NODE=4
DATASIZE1=128
DATASIZE2=128
GENERATION=10
NWORKER=3
CPUS_PER_WORKER=2

GR='\033[0;32m'
BL='\033[0;34m'
NC='\033[0m' # No Color

echo -n -e "${BL}WDIR"  
echo -e "${GR} $PWD${NC}"

echo -n -e "${BL}PDI"   
echo -e "${GR} `which pdirun`${NC}"

echo -n -e "${BL}MPI"   
echo -e "${GR} `which mpirun`${NC}"

echo -n -e "${BL}PYTHON"
echo -e "${GR} `which python`${NC}"

echo -n -e "${BL}RAY"   
echo -e "${GR} `which ray`${NC}"



# AUXILIAR VALUES
SIMUNODES=$(($PARALLELISM2 * $PARALLELISM1 / $MPI_PER_NODE)) # / MPI tasks per node
NNODES=$((1 + $NWORKER + $SIMUNODES)) # WORKERS + HEAD + SIMULATION
NPROC=$(($PARALLELISM2 * $PARALLELISM1 + $NNODES + 1))

# COMPILING
(CC=gcc CXX=g++ pdirun cmake .) > /dev/null 2>&1
pdirun make -B simulation

# MANAGING FILES
OUTPUT_DIR_NAME="outputs"
rm -rf $OUTPUT_DIR_NAME/ > /dev/null 2>&1
mkdir $OUTPUT_DIR_NAME

# RUNNING
CPUS=$(($CPUS_PER_WORKER * ($NWORKER + 1) + ($PARALLELISM1 * $PARALLELISM2) + $SIMUNODES))
echo Running in $PWD
`which python` prescript.py $DATASIZE1 $DATASIZE2 $PARALLELISM1 $PARALLELISM2 $GENERATION $NWORKER
export JOB_ID=$(sbatch --parsable -N $NNODES --ntasks=$NPROC Script.sh $SIMUNODES $MPI_PER_NODE $CPUS_PER_WORKER)

# /gpfs/users/fernandezx/spack/opt/spack/linux-centos7-cascadelake/gcc-11.2.0/python-3.10.8-gr23wncdlkfsy2ky42hcmljvrpvextag/lib/python3.10/site-packages/(.+?)\|(.+?)\|(.+?)\|
# ray memory --address $(cat address.var) > memory.log && ray status --address=$(cat address.var) > status.log