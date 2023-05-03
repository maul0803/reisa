import ray
import gc
import yaml
import time
import numpy as np


class ReisaArray(list):
    def __init__(self, *args):
        super().__init__(*args)
        self.accessed = []

    def __getitem__(self, i):
        self.accessed.append(i)
        return super().__getitem__(i)

class Reisa:
    def __init__(self, file, address):
        self.iterations = 0
        self.mpi_per_node = 0
        self.mpi = 0
        ray.init("ray://"+address+":10001")
        ray.timeline(filename="timeline-client.json")

        
        with open(file, "r") as stream:
            try:
                data = yaml.safe_load(stream)
                self.iterations = data["MaxtimeSteps"]
                self.mpi_per_node = data["mpi_per_node"]
                self.mpi = data["parallelism"]["height"] * data["parallelism"]["width"]
            except yaml.YAMLError as exc:
                print(exc)
        
        self.array = ReisaArray([i for i in range(self.iterations)])
        self.actors=list()

        i=0
        timeout=10
        while i<timeout:
            resources = ray.available_resources()
            if "actor" not in resources:
                break
            time.sleep(5)
            i = i + 1
        if i == timeout:
            raise Exception("Something is going wrong with the cluster. Client is exiting...")
            return
        for rank in range(0, self.mpi, self.mpi_per_node):
            self.actors.append(ray.get_actor("ranktor"+str(rank), namespace="mpi"))
            
        return

        
    def get_result(self, func):

            @ray.remote (max_retries=2, resources={"data":1}, scheduling_strategy="SPREAD")
            def remote_task(refs, par, i):
                return func(ray.get(refs))

            result = []
            for i in range(self.iterations):
                actor_references = [actor.trigger.remote(remote_task, i) for actor in self.actors]
                actors_answers = ray.get(actor_references) # actors_answers are still references
                result.append(remote_task.remote(actors_answers, 2, i))
                gc.collect()

            return result

    def shutdown(self):
        for actor in self.actors:
            actor.finish.remote()

        ray.shutdown()