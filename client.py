import time
import numpy as np
from  reisa import Reisa # Mandatory import
import os

# The user can decide which task is executed on each level of the following tree
# The user can decide to skip every level of the tree (more verbosity) on the data
# The first level of the tree is mandatory
# For example, if we skip actor, iter and global levels, we will get the results of all the process task executed
'''
process  process   p   p   p  p  p   p      # One task per process per iteration
    \      /        \  /    \  /  \  /
     \    /          \/      \/    \/
      actor          a        a     a       # One task per actor per iteration (typically gathering the results of the processes within the same node)
          \         /          \    /
           \       /            \  /
            \     /              \/
             iter               iter        # One task per iteration (typically gathering the results of all the actors in that iteration)
                \               /
                 \             /
                 global function            # Task executed over the received data (typically gathering the results of all the iterations)
'''

# Get infiniband address
address = os.environ.get("RAY_ADDRESS").split(":")[0]
# Starting reisa (mandatory)
handler = Reisa("config.yml", address)
    
# Process level
def process_func(rank: int, iter: int, queue):
    # "queue" will be the available data from "rank" process since the simulation has started (from iteration 0 to "iter")
    c0 = 2. / 3.
    data = queue.sublist(iter-5, iter) # Calling the queue we get the data (we can use just round/square brackets as well)
    data = np.array(data)
    return np.average(c0 / 1 * (data[3] - data[1] - (data[4] - data[0]) / 8.))

# We will skip this level on this example (so iter_func will receive a list of lists)
# def actor_func(rank: int, iter: int, process_results):
#     # Getting the results of the process_tasks thrown in the iteration "iter" on the node whose actor was created by process "rank".
#     return np.average(process_results())

# iter level
def iter_func(iter: int, actor_results):
    # Getting the results of the previous levels in iteration "iter"
    return np.average(actor_results())

# We will skip this level on this example (so, in this example, the user will receive one value per iteration stored in an array)
# def global_func(iter_results):
#     # Getting the results of every iteration
#     return np.average(iter_results[9])

# The iterations that will be executed (from 0 to end by default), in this case we will need 4 available timesteps
iterations = [i for i in range(5,handler.iterations)]

# Throw the analytics (blocking operation), kept iters paramerter means the iterations kept in memory before the last one
result = handler.get_result(process_func, actor_task=None, iter_task=iter_func, final_task=None, selected_iters=iterations, kept_iters=5)

# Write the results
with open("results.log", "a") as f:
    f.write("\nResult: "+str(result)+".\n")

# SIMUALTION MUST KNOW THAT THE ANALYTICS WERE FINISHED
handler.shutdown()