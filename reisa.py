def derivee(F, dx):
    c0 = 2. / 3.
    dFdx = c0 / dx * (F[3: - 1] - F[1: - 3] - (F[4:] - F[:- 4]) / 8.)
    return dFdx

# Called by yaml
def analytics(rank, data, iter):    
    return derivee(data, 1).mean()

# Called by yaml
def manageResults(iresults, iter):
    # In this case, we are adding up all the results for each iteration
    with open("results.log", "a") as f:
        local = 0
        for value in iresults:
            local = local + value
        if local==128*iter:
            f.write("\nIter "+str(iter)+" result: "+str(local)+".\n")
        else:
            f.write("\nError in iter "+str(iter)+" result: "+str(local)+".\n")
