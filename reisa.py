import ray
import gc
import yaml
import time

# "Background" code for the user

class Reisa:
    def __init__(self, file, address):
        self.iterations = 0
        self.mpi_per_node = 0
        self.mpi = 0
        self.workers = 0
        
        # Init Ray
        ray.init("ray://"+address+":10001")
       
        # Get the configuration of the simulatin
        with open(file, "r") as stream:
            try:
                data = yaml.safe_load(stream)
                self.iterations = data["MaxtimeSteps"]
                self.mpi_per_node = data["mpi_per_node"]
                self.mpi = data["parallelism"]["height"] * data["parallelism"]["width"]
                self.workers = data["workers"]
            except yaml.YAMLError as e:
                print(e)
        return
    
    def get_result(self, process_task, actor_task=None, iter_task=None, final_task=None, selected_iters=None, kept_iters=None):

            # This class will be the key to able the user to deserialize the data transparently
            class RayList(list):
                def __call__(self): # Round brackets operation like in "queue()", obtain all the data.
                    there_is_list = False # The array of data is an array of references
                    for item in self: # Check if there is another list within the list
                        if isinstance(item, RayList):
                            there_is_list = True
                            break

                    if there_is_list:
                        result=[]
                        for item in self: # If there are lists deserialize each element of the list
                            if isinstance(item, RayList):
                                result.append(item())
                            else:
                                result.append(ray.get(item))
                        return result
                    else: # If there is not lists (regular array of references) deserialize the whole array
                        return ray.get(self)

                def __getitem__(self, index): # Square brackets operation like in queue[3], obtain the selected data.
                    item = super().__getitem__(index)
                    if isinstance(item, RayList):
                        return item()
                    else:
                        return ray.get(item)
                
                def sublist(self, index1, index2): # Square brackets operation like in queue[3], obtain the selected data.
                    refs = RayList()
                    for i in range(index1, index2):
                        refs.append(super().__getitem__(i))
                    return refs()
            
            # Create the remote ray tasks from user functions, resources "data=1" means executed on computing nodes
            if process_task:
                process_task = ray.remote(max_retries=2, resources={"data":1}, scheduling_strategy="DEFAULT")(process_task)
            else:
                raise Exception("process_task cannot be None.")
                return
            if actor_task:
                actor_task = ray.remote(max_retries=2, resources={"data":1}, scheduling_strategy="DEFAULT")(actor_task)
            if iter_task:
                iter_task = ray.remote(max_retries=2, resources={"data":1}, scheduling_strategy="DEFAULT")(iter_task)
            if final_task:
                final_task = ray.remote(max_retries=2, resources={"data":1}, scheduling_strategy="DEFAULT")(final_task)
            if selected_iters is None:
                selected_iters = [i for i in range(self.iterations)]
            if kept_iters is None:
                kept_iters = int(self.iterations/4*3)
                   
            results = RayList([ray.put(None) for i in range(self.iterations)])
            actors = self.get_actors()
            start = 0
            
            for i in selected_iters:
                # Ask each actor to execute "mpi_per_node" processes_task and one actor_task if requested by the user
                actor_references = [actor.trigger.remote(process_task, actor_task, i, RayList, kept_iters) for actor in actors]
                # Get the answer of the actors, remember that the actors are sending back the references of the thrown tasks (future results)
                actors_answers = RayList(ray.get(actor_references))
                if i == selected_iters[0]:
                    start = time.time()
                # Execute iter_task if requested by the user and store the result
                if iter_task:
                    results[i] = iter_task.remote(iter, actors_answers)
                else:
                    results[i] = actors_answers

            # Execute global task if requested by the user and return the value
            if final_task:
                tmp = ray.get(final_task.remote(results))
            else:
                tmp = results()

            print("{:<21}".format("ANALYTICS_TIME:") + "{:.5f}".format(time.time()-start) + " (avg:"+"{:.5f}".format((time.time()-start)/self.iterations)+")")
            return tmp

    # Mark the analytics as finished
    def shutdown(self):
        self.get_actors()
        for actor in self.actors:
            actor.finish.remote()
        
        ray.timeline(filename="timeline-client.json")
        ray.shutdown()

    # Get the actors created by the simulation
    def get_actors(self):
        timeout = 60
        start_time = time.time()
        error = True
        self.actors = list()
        while error:
            try:
                for rank in range(0, self.mpi, self.mpi_per_node):
                    self.actors.append(ray.get_actor("ranktor"+str(rank), namespace="mpi"))
                error = False
            except Exception as e:
                self.actors=list()
                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time >= timeout:
                    raise Exception("Cannot get the Ray actors. Client is exiting")
            time.sleep(1)
        return self.actors