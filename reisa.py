def derivee(F, dx):
    c0 = 2. / 3.
    dFdx = c0 / dx * (F[3: - 1] - F[1: - 3] - (F[4:] - F[:- 4]) / 8.)
    return dFdx

# Called by yaml
def analytics(rank, data, iter):    
    return derivee(data, 1).mean()

# Called by yaml
def manageResults(allresults, np, max):
    # In this case, we are adding up all the results for each iteration
    with open("results.log", "w") as f:
        for i in range(max):
            local = 0
            for p in range(np):
                local = local + allresults[p][i]
            f.write("\nIter "+str(i)+" result: "+str(local)+".\n")
