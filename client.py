import time
import numpy as np
from  reisa import Reisa # Mandatory import
import os

# The user can decide which task is executed on each level of the following tree
'''
    p0 p1 p2 p3   p0 p1 p2 p3      # One task per process per iteration
    \  /   \  /    \  /  \  /
     \/     \/      \/    \/
     iteration 0  iteration 1      # One task per iteration (typically gathering the results of all the actors in that iteration)
          \          /
           \        /
            \      /
             result                # Array with iteration-level results
'''

# Get infiniband address
address = os.environ.get("RAY_ADDRESS").split(":")[0]
# Starting reisa (mandatory)
handler = Reisa("config.yml", address)
    
# Process-level analytics code
def process_func(rank: int, i: int, queue):
    # "queue" will be the available data for "rank" process since the simulation has started (from iteration 0 to "i")
    # We must take into acount that some data will be erased to free memory
    c0 = 2. / 3.
    dx = 1
    data = queue[-5:] # Using square brackets to select the data
    F = np.array(data)
    dFdx = np.average(c0 / dx * (F[3: - 1] - F[1: - 3] - (F[4:] - F[:- 4]) / 8.))
    return dFdx

# Iteration-level analytics code
def iter_func(i: int, process_results):
    res = np.average(process_results[i][:]) # get the data with square brackets
    return res

# The iterations that will be executed (from 0 to end by default), in this case we will need 4 available timesteps
iterations = [i for i in range(4, handler.iterations)]

# Launch the analytics (blocking operation), kept iters paramerter means the number of iterations kept in memory before the current iteration
result = handler.get_result(process_task=process_func, iter_task=iter_func, selected_iters=iterations, kept_iters=5, timeline=True)

# Write the results
with open("results.log", "a") as f:
    f.write("\nResult: "+str(result)+".\n")


