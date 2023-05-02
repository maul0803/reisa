import ray
import time
import gc
import numpy as np
from  reisa import Reisa

handler = Reisa("config.yml", "localhost")

result = []
start = time.time()

for i in range(10):
    
    def func(data):
        return np.sum(data[i])

    result.append(handler.get_result(func))

result = ray.get(result)
end = time.time()

for i in range(10):
    with open("results.log", "a") as f:
        f.write("\nResult: "+str(result[i])+".\n")
        

print("{:<21}".format("ANALYTICS_TIME:") + "{:.5f}".format(end-start) + " (avg:"+"{:.5f}".format((end-start)/handler.iterations)+")")
# print("{:<21}".format("ANL_ITER_TIME:") + str(iter_times))
print("{:<21}".format("IN_SITU_PROCESSING:") + "Disable")

handler.shutdown()