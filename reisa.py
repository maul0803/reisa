from datetime import datetime
from math import ceil
import itertools
import yaml
import time
import ray
import sys
import gc
import os

def eprint(*args, **kwargs):
    """
    Print messages to the standard error stream.

    :param args: Positional arguments to print.
    :param kwargs: Keyword arguments for the print function.
    """
    print(*args, file=sys.stderr, **kwargs)

# "Background" code for the user

# This class will be the key to able the user to deserialize the data transparently
class RayList(list):
    """
    A custom list that interacts with Ray objects, allowing for transparent
    deserialization of remote references.
    """

    def __call__(self, index): # Square brackets operation to obtain the data behind the references.
        """
        Retrieve data from Ray references when accessed via square brackets.

        :param index: The index or slice of the list to retrieve.
        """
        item = super().__getitem__(index)
        if isinstance(index, slice):
            free(item)
        else:
            free([item])

    def __getitem__(self, index): # Square brackets operation to obtain the data behind the references.
        """
        Get an item from the list while retrieving Ray objects.

        :param index: Index or slice to retrieve.
        :return: The retrieved item(s).
        """
        item = super().__getitem__(index)
        if isinstance(index, slice):
            return ray.get(RayList(item))
        else:
            return ray.get(item)

class Reisa:
    """
    A class that initializes and manages a Ray-based simulation environment.
    """

    def __init__(self, file, address):
        """
        Initialize the Reisa simulation by reading configuration parameters
        from a YAML file and setting up Ray.

        :param file: Path to the YAML configuration file.
        :param address: Address of the Ray cluster.
        """
        self.iterations = 0
        self.mpi_per_node = 0
        self.mpi = 0
        self.datasize = 0
        self.workers = 0
        self.actors = list()
        
        # Initialize Ray
        if os.environ.get("REISA_DIR"):
            ray.init("ray://"+address+":10001", runtime_env={"working_dir": os.environ.get("REISA_DIR")})
        else:
            ray.init("ray://"+address+":10001", runtime_env={"working_dir": os.environ.get("PWD")})
       
        # Load simulation configuration
        with open(file, "r") as stream:
            try:
                data = yaml.safe_load(stream)
                self.iterations = data["MaxtimeSteps"]
                self.mpi_per_node = data["mpi_per_node"]
                self.mpi = data["parallelism"]["height"] * data["parallelism"]["width"]
                self.workers = data["workers"]
                self.datasize = data["global_size"]["height"] * data["global_size"]["width"]
            except yaml.YAMLError as e:
                eprint(e)

        return
    
    def get_result(self, process_func, iter_func, global_func=None, selected_iters=None, kept_iters=None, timeline=False):
        """
        Execute a simulation and collect results.

        :param process_func: Function to process individual simulation steps.
        :param iter_func: Function to process iterations.
        :param global_func: (Optional) Function to process all results at the end.
        :param selected_iters: (Optional) List of iterations to execute.
        :param kept_iters: (Optional) Number of iterations to keep in memory.
        :param timeline: (Optional) If True, generate a Ray timeline.
        :return: Processed results as a dictionary or global function output.
        """
        max_tasks = ray.available_resources()['compute']
        actors = self.get_actors()
        
        if selected_iters is None:
            selected_iters = [i for i in range(self.iterations)]
        if kept_iters is None:
            kept_iters = self.iterations

        # process_task = ray.remote(max_retries=-1, resources={"compute":1}, scheduling_strategy="DEFAULT")(process_func)
        # iter_task = ray.remote(max_retries=-1, resources={"compute":1, "transit":0.5}, scheduling_strategy="DEFAULT")(iter_func)

        @ray.remote(max_retries=-1, resources={"compute":1}, scheduling_strategy="DEFAULT")
        def process_task(rank: int, i: int, queue):
            """
            Remote function to process a simulation step.

            :param rank: Rank of the process.
            :param i: Current iteration.
            :param queue: Data queue containing simulation values.
            :return: Processed result.
            """
            return process_func(rank, i, queue)
            
        iter_ratio=1/(ceil(max_tasks/self.mpi)*2)

        @ray.remote(max_retries=-1, resources={"compute":1, "transit":iter_ratio}, scheduling_strategy="DEFAULT")
        def iter_task(i: int, actors):
            """
            Remote function to process an iteration.

            :param i: Current iteration index.
            :param actors: list of Ray actors managing the simulation.
            :return: Processed iteration result.
            """
            current_results = [actor.trigger.remote(process_task, i) for j, actor in enumerate(actors)]
            current_results = ray.get(current_results)
            
            if i >= kept_iters-1:
                [actor.free_mem.remote(current_results[j], i-kept_iters+1) for j, actor in enumerate(actors)]
            
            return iter_func(i, RayList(itertools.chain.from_iterable(current_results)))

        start = time.time() # Measure time
        results = [iter_task.remote(i, actors) for i in selected_iters]
        ray.wait(results, num_returns=len(results)) # Wait for the results

        eprint("{:<21}".format("EST_ANALYTICS_TIME:") + "{:.5f}".format(time.time() - start) +
               " (avg:" + "{:.5f}".format((time.time() - start) / self.iterations) + ")")

        if global_func:
            return global_func(RayList(results))
        else:
            tmp = ray.get(results)
            output = {selected_iters[i]: tmp[i] for i in range(len(selected_iters)) if tmp[i] is not None}

            if timeline:
                ray.timeline(filename="timeline-client.json")

            return output

    def get_actor(self):
        """
        Retrieve the Ray actors managing the simulation.

        :return: A list of Ray actors.
        :raises Exception: If one of the Ray actors is not available after a timeout period.
        """
        timeout = 60
        start_time = time.time()
        self.actors = list()
        while True:
            try:
                for rank in range(0, self.mpi, self.mpi_per_node):
                    self.actors.append(ray.get_actor("ranktor"+str(rank), namespace="mpi"))
                return self.actors
            except Exception:
                self.actors = list()
                if time.time() - start_time >= timeout:
                    raise Exception("Cannot get the Ray actors. Client is exiting.")
            time.sleep(1)



    def shutdown(self):
        """
        Shut down the simulation by killing the Ray actors and shutting down Ray.

        :return: None
        """
        if self.actors:
            for actor in self.actors:
                ray.kill(actor)
            ray.shutdown()