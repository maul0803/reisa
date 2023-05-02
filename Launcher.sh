#!/bin/bash

# spack load pdiplugin-pycall@1.6.0 pdiplugin-mpi@1.6.0;

MAIN_DIR=$PWD

GR='\033[0;32m'
BL='\033[0;34m'
NC='\033[0m' # No Color

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
PARALLELISM1=4
PARALLELISM2=4
MPI_PER_NODE=2

# DATASIZE
DATASIZE1=$((4000*$PARALLELISM1))
DATASIZE2=$((4000*$PARALLELISM2))

# STEPS
GENERATION=10

# ANALYTICS HARDWARE
WORKER_NODES=$(($PARALLELISM1*$PARALLELISM2/4))
CPUS_PER_WORKER=24
WORKER_THREADING=2 # DEISA uses 24 Threads/worker, 2 workers/node -> 48 threads per node -> 12 Threads per MPI/process

#WORKER CORES IN SIMULATION NODES
CORES_IN_SITU=10

# for SIZE in 6 8 10 12 14
# do
#     DATASIZE1=$((2**$SIZE))
#     DATASIZE2=$DATASIZE1
    
#     for PARALLELISM in 4 8 16 64 128
#     do
#         case $PARALLELISM in 
        
#             128) 
#                 PARALLELISM1=16
#                 PARALLELISM2=8
#                 MPI_PER_NODE=8
#                 ;;
#             64)
#                 PARALLELISM1=8
#                 PARALLELISM2=8
#                 MPI_PER_NODE=8
#                 ;;
#             16)
#                 PARALLELISM1=4
#                 PARALLELISM2=4
#                 MPI_PER_NODE=4
#                 ;;
#             8)
#                 PARALLELISM1=4
#                 PARALLELISM2=2
#                 MPI_PER_NODE=4
#                 ;;
#             *)
#                 PARALLELISM1=2
#                 PARALLELISM2=2
#                 MPI_PER_NODE=4
#                 ;;
#         esac

#         for ITER in 10 50 100 500 1000
#         do
#             GENERATION=$ITER

#             for WCPU in 2 4 8 16 32 64
#             do
#                 case $WCPU in 
                
#                     64) 
#                         WORKER_NODES=8
#                         CPUS_PER_WORKER=8
#                         ;;
#                     32)
#                         WORKER_NODES=8
#                         CPUS_PER_WORKER=4
#                         ;;
#                     16)
#                         WORKER_NODES=2
#                         CPUS_PER_WORKER=8
#                         ;;
#                     8)
#                         WORKER_NODES=2
#                         CPUS_PER_WORKER=4
#                         ;;
#                     4)
#                         WORKER_NODES=2
#                         CPUS_PER_WORKER=2
#                         ;;
#                     *)
#                         WORKER_NODES=1
#                         CPUS_PER_WORKER=2
#                         ;;
#                 esac

                # AUXILIAR VALUES
                SIMUNODES=$(($PARALLELISM2 * $PARALLELISM1 / $MPI_PER_NODE)) # / MPI tasks per node
                NNODES=$(($WORKER_NODES + $SIMUNODES + 1)) # WORKERS + HEAD + SIMULATION
                NPROC=$(($PARALLELISM2 * $PARALLELISM1 + $NNODES + 1))

                # MANAGING FILES
                date=$(date +%Y-%m-%d_%X)
                OUTPUT=outputs/$date
                `which python` prescript.py $DATASIZE1 $DATASIZE2 $PARALLELISM1 $PARALLELISM2 $GENERATION $WORKER_NODES $MPI_PER_NODE $CPUS_PER_WORKER $CORES_IN_SITU $WORKER_THREADING
                mkdir -p $OUTPUT
                mkdir logs 2>/dev/null
                touch logs/jobs.log
                cp *.yml client.py reisa.py simulation Script.sh $OUTPUT

                # RUNNING
                cd $OUTPUT
                echo $1 > comment.txt
                echo -e "Executing $(sbatch --parsable --qos=normal -N $NNODES --ntasks=$NPROC Script.sh $SIMUNODES $MPI_PER_NODE $CPUS_PER_WORKER $CORES_IN_SITU $WORKER_THREADING) in $OUTPUT" >> $MAIN_DIR/logs/jobs.log
                cd $MAIN_DIR
                sleep 1
#             done
#         done
#     done
# done