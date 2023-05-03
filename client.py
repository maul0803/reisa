import ray
import time
import gc
import numpy as np
from  reisa import Reisa
import os

address = os.environ.get("RAY_ADDRESS").split(":")[0]
handler = Reisa("config.yml", address)

result = []
    
def func(data):
    return np.sum(data)

start = time.time()
result = handler.get_result(func)
result = ray.get(result)
end = time.time()

for i in range(handler.iterations):
    with open("results.log", "a") as f:
        f.write("\nResult: "+str(result[i])+".\n")
        

print("{:<21}".format("ANALYTICS_TIME:") + "{:.5f}".format(end-start) + " (avg:"+"{:.5f}".format((end-start)/handler.iterations)+")")
# print("{:<21}".format("ANL_ITER_TIME:") + str(iter_times))
print("{:<21}".format("IN_SITU_PROCESSING:") + "Disable")

handler.shutdown()