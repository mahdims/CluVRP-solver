
from gurobipy import *
from itertools import combinations
import numpy as np
import sys
# Callback - use lazy constraints to eliminate sub-tours


def subtourelim(model, where):

    if where == GRB.callback.MIPSOL:
        selected = []
        sol = {}
        # make a list of edges selected in the solution
        for i, j in model._vars.keys():
            sol[i,j] = model.cbGetSolution(model._vars[i,j])
            if sol[i,j] > 0.5:
                selected.append( (i,j) )
        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        if len(tour) < N:
            # add a subtour elimination constraint
            expr = 0
            for i in range(len(tour)):
                for j in range(len(tour)):
                    if j != i:
                        expr += model._vars[tour[i], tour[j]]
            model.cbLazy(expr <= len(tour)-1)

# Given a list of edges, finds the shortest subtour
def subtour(edges):
    visited = {}
    selected = {}
    for i in Gnodes:
        visited[i] = False
        selected[i] = []
    cycles = []
    lengths = []

    for x,y in edges:
        selected[x].append(y)

    while True:
        current = list(visited.keys())[list(visited.values()).index(False)]
        thiscycle = [current]

        while True:
              visited[current] = True
              neighbors = [x for x in selected[current] if not visited[x]]
              if len(neighbors) == 0:
                    break
              current = neighbors[0]
              thiscycle.append(current)
        cycles.append(thiscycle)
        lengths.append(len(thiscycle))

        if sum(lengths) == N:
            break

    return cycles[lengths.index(min(lengths))]


def Route_correction(Sequence):
    # Sequence Correction. Since we solve a TSP start and end of the Hamiltonion path should be adjusted
    inx_s = np.where(np.array(Sequence) == "D0")[0][0]
    if inx_s == len(Sequence) - 1:  # when the start of the sequence is at the last position
        if Sequence[0] == "D1":  # easy the end is at the first just reverse every thing
            Sequence.reverse()
        if Sequence[inx_s - 1] == "D1":  # 180 degree the opposite of what we need
            Sequence = Sequence[inx_s:] + Sequence[:inx_s]
    else:
        if Sequence[inx_s + 1] == "D1":
            inx_e = inx_s + 1
            Sequence = Sequence[:inx_e][::-1] + Sequence[inx_e:][::-1]
        if Sequence[inx_s - 1] == "D1":
            Sequence = Sequence[inx_s:] + Sequence[:inx_s]
    return Sequence

def TSP_model(dis,Nodes):
    global Gnodes, N
    Gnodes=list(Nodes.keys())
    N = len(Gnodes)
    Big_m =  max(dis.values())
    dis["D0", "D1"] = dis["D1", "D0"] = -1 * Big_m

    if N <= 3:
        D0 = Nodes.pop("D0")
        D1 = Nodes.pop("D1")
        customer = list(Nodes.keys())[0]
        route = ["D0", customer, "D1"]
        return route , dis[("D0", customer)] + dis[(customer,"D1")]

    TSP = Model("Tsp")
    
    # Create variables
    
    x = {}
    for i,j in dis.keys():
         x[i,j] = TSP.addVar(obj=dis[i, j], vtype=GRB.BINARY, name='e'+str(i)+'_'+str(j))
         #x[j,i] = TSP.addVar(obj=dis[j, i], vtype=GRB.BINARY, name='e'+str(j)+'_'+str(i))

    TSP._vars = x
    TSP.update()
    # Add flow balance constraints
    TSP.addConstrs(quicksum(x[i,j] for i in Gnodes if j != i) == 1 for j in Gnodes)
    TSP.addConstrs(quicksum(x[i,j] for j in Gnodes if j != i) == 1 for i in Gnodes)
        
    TSP.update()
    # Optimize model
    TSP.Params.OutputFlag=0
    TSP.params.LazyConstraints = 1
    TSP.optimize(subtourelim)
    if TSP.status != 2:
        print("TSP is not feasible")
        return Gnodes
    solution = TSP.getAttr('x', x)
    selected = [(i,j) for i,j in x.keys() if solution[i,j] > 0.5]
    route = subtour(selected)
    if len(route) != N :
        sys.exit(Gnodes)
    route = Route_correction(route)
    return route, (TSP.Objval + Big_m)
