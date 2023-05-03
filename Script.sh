#!/bin/bash
#SBATCH --time=01:00:00
#SBATCH -o reisa.log
#SBATCH --error reisa.log
#SBATCH --mem-per-cpu=4GB
#SBATCH --wait-all-nodes=1
# #SBATCH --oversubscribe
# #SBATCH --overcommit
#SBATCH --exclusive
###################################################################################################
inicio=$(date +%s%N)

echo -e "Slurm job started at $(date +%d/%m/%Y_%X)\n"
unset RAY_ADDRESS;
export RAY_record_ref_creation_sites=1
export RAY_SCHEDULER_EVENTS=0
export OMP_NUM_THREADS=1
export RAY_memory_usage_threshold=0.8
export RAY_PROFILING=1
export RAY_task_events_report_interval_ms=200
# export RAY_BACKEND_LOG_LEVEL=debug
REDIS_PASSWORD=$(uuidgen)
export REDIS_PASSWORD


export MPI_TASKS=$(($SLURM_NTASKS - $SLURM_NNODES - 1))
export MPI_PER_NODE=$2
NUM_SIM_NODES=$1
WORKER_NUM=$(($SLURM_JOB_NUM_NODES - 1 - $NUM_SIM_NODES))
export CPUS_PER_WORKER=$3
CORES_IN_SITU=$4
REISA_THREADING=$5


# Setting nodes
NODES=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
NODES_ARRAY=($NODES)
SIMARRAY=(${NODES_ARRAY[@]:$WORKER_NUM+1:$NUM_SIM_NODES});

for nodo in ${SIMARRAY[@]}; do
  SIM_NODE_LIST+="$nodo,"
done
SIM_NODE_LIST=${SIM_NODE_LIST%,}

echo -e "Initing Ray (1 head node + $WORKER_NUM worker nodes + $NUM_SIM_NODES simulation nodes) on nodes: \n\t${NODES_ARRAY[@]}"

head_node=${NODES_ARRAY[0]}
head_node_ip=$(srun -N 1 -n 1 --relative=0 echo $(ip -f inet addr show ib0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') &)
port=6379
echo -e "Head node: $head_node_ip:$port\n"
export RAY_ADDRESS=$head_node_ip:$port

# Launching the head node
srun --nodes=1 --ntasks=1 --relative=0 --cpus-per-task=$CPUS_PER_WORKER \
    ray start --head --node-ip-address="$head_node_ip" --port=$port --redis-password "$REDIS_PASSWORD" --disable-usage-stats\
    --num-cpus $CPUS_PER_WORKER --block --resources='{"data": 0}'  1>/dev/null 2>&1 &
echo $RAY_ADDRESS > address.var

cnt=0
k=0
max=10
 # Wait for head node
while [ $cnt -lt 1 ] && [ $k -lt $max ]; do
    sleep 5
    cnt=$(ray status --address=$RAY_ADDRESS 2>/dev/null | grep -c node_)
    k=$((k+1))
done

# Launch Ray workers
for ((i = 1; i <= WORKER_NUM; i++)); do
    node_i=${NODES_ARRAY[$i]}

    srun --nodes=1 --ntasks=1 --relative=$i --cpus-per-task=$CPUS_PER_WORKER --threads-per-core=$REISA_THREADING\
        ray start --address $RAY_ADDRESS --redis-password "$REDIS_PASSWORD"\
        --num-cpus $(($CPUS_PER_WORKER*$REISA_THREADING)) --block --resources='{"data": 100}' --object-store-memory $((10*10**9))  1>/dev/null 2>&1 &
done
    
# Launch Ray instance in simulation nodes
for ((; i < $SLURM_JOB_NUM_NODES; i++)); do
    node_i=${NODES_ARRAY[$i]}
    srun  --nodes=1 --ntasks=1 --relative=$i -c $CORES_IN_SITU\
      ray start --address $RAY_ADDRESS --block --resources='{"actor": 1}' --object-store-memory $((10*10**9)) 1>/dev/null 2>&1 &
done

cnt=0
k=0
max=10
 # Wait for all the nodes have join the cluster
while [ $cnt -lt $SLURM_JOB_NUM_NODES ] && [ $k -lt $max ]; do
    sleep 5
    cnt=$(ray status --address=$RAY_ADDRESS 2>/dev/null | grep -c node_)
    k=$((k+1))
done
fin=$(date +%s%N)

ray status --address=$RAY_ADDRESS

# Launch the simulation code (python script is here)
# echo -e "Running simulation in: $SIM_NODE_LIST"
pdirun srun --oversubscribe --overcommit -N $NUM_SIM_NODES --ntasks-per-node=$MPI_PER_NODE\
    -n $MPI_TASKS --nodelist=$SIM_NODE_LIST --cpus-per-task=1\
        ./simulation $SLURM_JOB_ID &
sim=$!

# Running client on head node
srun --oversubscribe --overcommit --nodes=1 --ntasks=1 --relative=0 -c 1\
    `which python` client.py --ray-timeline &

duracion=$((fin-inicio))
duracion=$(bc <<< "scale=5; $duracion/1000000000")
sleep 1
printf "\n%-21s%s\n" "RAY_DEPLOY_TIME:" "$duracion"

# Wait for results
wait $sim
echo -e "\nSlurm job finished at $(date +%d/%m/%Y_%X)"
