import ray
import os
import yaml
import time
import itertools
import gc
import numpy as np

iterations = 0
mpi_per_node = 0
mpi = 0

with open("config.yml", "r") as stream:
    try:
        data = yaml.safe_load(stream)
        iterations = data["MaxtimeSteps"]
        mpi_per_node = data["mpi_per_node"]
        mpi = data["parallelism"]["height"] * data["parallelism"]["width"]
    except yaml.YAMLError as exc:
        print(exc)

address=os.environ.get("RAY_ADDRESS").split(":")[0]
# print("Client connecting to " + address)

ray.init("ray://localhost:10001")

def func(data):
    return np.sum(data)

in_situ = False
@ray.remote (max_retries=2, resources={"data":1})
def remote_sum(data):
    # print(data)
    return func(ray.get(data))

@ray.remote (max_retries=2, resources={"data":1})
def sum_actor_data(actor_data):
    # Here we receive a list with "mpi_per_node" length
    actor_result = [remote_sum.remote([data]) for data in actor_data]
    return func(ray.get(actor_result))

while True:
    resources = ray.available_resources()
    if "actor" not in resources:
        break
    time.sleep(5)
    
actors = list()
for rank in range(0, mpi, mpi_per_node):
    actors.append(ray.get_actor("ranktor"+str(rank), namespace="mpi"))

iter_times=[]
start = time.time()
for i in range(iterations):
    start_iter = time.time()
    task_ref = [sum_actor_data.remote(actor.get_iter.remote(i)) for actor in actors] # Recursos neste método para que as iteracións non bloqueen
    with open("results.log", "a") as f:
        f.write("\nIter "+str(i)+" result: "+str(ray.get(remote_sum.remote(task_ref)))+".\n")
    iter_times.append(time.time() - start_iter)
    gc.collect()

end = time.time()
print("{:<21}".format("ANALYTICS_TIME:") + str(end-start))
print("{:<21}".format("ANL_ITER_TIME:") + str(iter_times))
print("{:<21}".format("IN_SITU_PROCESSING:") + str(in_situ))

for actor in actors:
    actor.finish.remote()

ray.shutdown()