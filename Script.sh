#!/bin/bash
#SBATCH --time=00:05:00
#SBATCH -o reisa.log
#SBATCH --error reisa.log
#SBATCH --mem-per-cpu=2GB
#SBATCH --wait-all-nodes=1
#SBATCH --oversubscribe
#SBATCH --exclusive
###################################################################################################

unset RAY_ADDRESS;

mpi_tasks=$(($SLURM_NTASKS - $SLURM_NNODES - 1))
mpi_per_node=$2
num_sim_nodes=$1
worker_num=$(($SLURM_JOB_NUM_NODES - 1 - $num_sim_nodes))
cpus_per_worker=$3


# Setting nodes
nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
nodes_array=($nodes)
simarray=(${nodes_array[@]: -$num_sim_nodes});

for nodo in ${simarray[@]}; do
  simunodelist+="$nodo,"
done
simunodelist=${simunodelist%,}

echo All nodes: ${nodes_array[@]} "(head node + $worker_num workers + $num_sim_nodes simulation nodes)"
echo Simulation nodes: ${simarray[@]} "($mpi_per_node MPI tasks on each node)"

head_node=${nodes_array[0]}
head_node_ip=$(srun -N 1 -n 1 --relative=0 hostname -i &)
port=6380
export CLIENT_PORT=20001
echo -e "Head node: $head_node_ip:$port"


# Launching the head node
srun --nodes=1 --ntasks=1 --relative=0 --cpus-per-task=$cpus_per_worker \
    ray start --head --node-ip-address="$head_node_ip" --port=$port  --ray-client-server-port=$CLIENT_PORT\
    --num-cpus $cpus_per_worker --block  --resources='{"data": 0}' &
export RAY_ADDRESS=$head_node_ip:$port
sleep 15

# Launch Ray workers
for ((i = 1; i <= worker_num; i++)); do
    node_i=${nodes_array[$i]}
    echo "Starting worker node at $node_i"
    srun --nodes=1 --ntasks=1 --relative=$i --cpus-per-task=$cpus_per_worker \
        ray start --address $RAY_ADDRESS \
        --num-cpus $cpus_per_worker --block --resources='{"data": 1}' &
done
    
if [ $num_sim_nodes = 1 ]; then
  rel=$i
else
  rel="$i-$(($SLURM_JOB_NUM_NODES - 1))"
fi

# Launch Ray instance in simulation nodes
# echo "Starting simulation at $simunodelist"
# for ((; i < $SLURM_JOB_NUM_NODES; i++)); do
#     node_i=${nodes_array[$i]}
#     srun --mem-per-cpu=1GB --nodes=1 --ntasks=1 --relative=$i \
#         ray start --address $RAY_ADDRESS --block &
# done

sleep 10
export HN_ADDRESS=$RAY_ADDRESS
export MPI_PER_NODE=$mpi_per_node
unset RAY_ADDRESS
# Launch the simulation code (python script is here)
srun --exclusive --oversubscribe -N $num_sim_nodes --ntasks-per-node=$mpi_per_node \
    -n $mpi_tasks -c 2 --nodelist=$simunodelist --cpus-per-task=1 \
        pdirun ./simulation &
sim_pid=$!

# Wait for results
wait $sim_pid
echo "Finished"
