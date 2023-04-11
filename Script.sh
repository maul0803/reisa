#!/bin/bash
#SBATCH --time=00:15:00
#SBATCH -o reisa.log
#SBATCH --error reisa.log
#SBATCH --mem-per-cpu=1GB
##SBATCH --wait-all-nodes=1
#SBATCH --oversubscribe
#SBATCH --overcommit
## SBATCH --exclusive
#SBATCH --export=ALL
###################################################################################################

unset RAY_ADDRESS;
export RAY_record_ref_creation_sites=1
export RAY_SCHEDULER_EVENTS=0
export OMP_NUM_THREADS=1
# export RAY_BACKEND_LOG_LEVEL=warning
redis_password=$(uuidgen)
export redis_password


export mpi_tasks=$(($SLURM_NTASKS - $SLURM_NNODES - 1))
export mpi_per_node=$2
num_sim_nodes=$1
worker_num=$(($SLURM_JOB_NUM_NODES - 1 - $num_sim_nodes))
export cpus_per_worker=$3


# Setting nodes
nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
nodes_array=($nodes)
simarray=(${nodes_array[@]: -$num_sim_nodes});

for nodo in ${simarray[@]}; do
  simunodelist+="$nodo,"
done
simunodelist=${simunodelist%,}

echo -e Running example on nodes: ${nodes_array[@]} "(head node + $worker_num workers + $num_sim_nodes simulation nodes)\n"
echo -e Simulation nodes: ${simarray[@]} "($mpi_per_node MPI tasks on each node)\n"

head_node=${nodes_array[0]}
head_node_ip=$(srun -N 1 -n 1 --relative=0 hostname -i &)
port=6379
echo -e "Head node: $head_node_ip:$port\n"
export RAY_ADDRESS=$head_node_ip:$port

# `which python` set_cluster.py ${nodes_array[@]} && ray up cluster.yaml -y

# Launching the head node
srun --nodes=1 --ntasks=1 --relative=0 --cpus-per-task=$cpus_per_worker \
    ray start --head --node-ip-address="$head_node_ip" --port=$port --redis-password "$redis_password" --include-dashboard True\
    --num-cpus $cpus_per_worker --block  --resources='{"data": 10}'  1>/dev/null 2>&1 &
echo $RAY_ADDRESS > address.var
sleep 15

# Launch Ray workers
for ((i = 1; i <= worker_num; i++)); do
    node_i=${nodes_array[$i]}
    echo "Starting worker node at $node_i"
    srun --nodes=1 --ntasks=1 --relative=$i --cpus-per-task=$cpus_per_worker\
        ray start --address $RAY_ADDRESS --redis-password "$redis_password"\
        --num-cpus $cpus_per_worker --block --resources='{"data": 100}' 1>/dev/null 2>&1 &
done
    
if [ $num_sim_nodes = 1 ]; then
  rel=$i
else
  rel="$i-$(($SLURM_JOB_NUM_NODES - 1))"
fi

# Launch Ray instance in simulation nodes
echo "Starting simulation at $simunodelist"
for ((; i < $SLURM_JOB_NUM_NODES; i++)); do
    node_i=${nodes_array[$i]}
    srun --nodes=1 --ntasks=1 --relative=$i -c 2 \
        ray start --address $RAY_ADDRESS --block --num-cpus=2 --resources='{"mpi": 1}'  1>/dev/null 2>&1 &
done


 cnt=$(ray status | grep node_ | wc -l)
 i=0
 max=100
 
 # Wait for all the nodes have join the cluster
 while [ $cnt -lt $SLURM_JOB_NUM_NODES ] && [ $iteraciones -lt $max_iteraciones ]; do
    sleep 5
    cnt=$(ray status --address=$RAY_ADDRESS | grep -c node_)
    i=$((i+1))
 done


# Launch the simulation code (python script is here)
pdirun srun --distribution=block:block --exclusive --oversubscribe -N $num_sim_nodes --ntasks-per-node=$mpi_per_node \
    -n $mpi_tasks --nodelist=$simunodelist --cpus-per-task=1\
        ./simulation &
sim_pid=$!

# Wait for results
wait $sim_pid
echo "Slurm job finished"
