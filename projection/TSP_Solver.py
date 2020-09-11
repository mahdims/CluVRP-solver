
import networkx as nx 
from gurobipy import *
from itertools import combinations


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

    current = "D0"
    while True:
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

        if sum(lengths) == n:
            break
        current = list(visited.keys())[list(visited.values()).index(False)]
    return cycles[lengths.index(min(lengths))]


def TSP_model(dis, Nodes, start_time):

    global Gnodes , n
    Gnodes = Nodes.keys()
    n = len(Gnodes)
    if n == 3:
        D0 = Nodes.pop("D0")
        D1 = Nodes.pop("D1")
        customer = list(Nodes.keys())[0]
        route = ["D0", customer, "D1"]
        return route, sum(dis.values()) + Nodes[customer].service_time

    BigM = max(dis.values()) + max([cus.service_time for cus in Nodes.values()]) + Nodes["D1"].TW[1]

    TSP = Model("Tsp")
    
    # Create variables
    
    x = tupledict()
    t = TSP.addVars(Gnodes, name="t")

    for i,j in dis.keys():
        x[i,j] = TSP.addVar(obj=0, vtype=GRB.BINARY, name='e'+str(i)+'_'+str(j))

    TSP.update()
    # The objective function that minimize the tour completion time
    TSP.setObjective(t["D1"], GRB.MINIMIZE)
    # Add flow balance constraints
    TSP.addConstrs(quicksum(x.select("*",j)) == 1 for j in Gnodes if j != "D0")
    TSP.addConstrs(quicksum(x.select(i,"*")) == 1 for i in Gnodes if i != "D1")
    # the MTY constraint to calculate the visit time to a node
    TSP.addConstrs(t[j] >= t[i] + Nodes[i].service_time + dis[i,j] + (x[i,j] - 1)*BigM for i,j in x.keys() if j != "D0" and i != "D1")
    TSP.addConstrs(t[i] <= Nodes[i].TW[1] for i in Gnodes if i != "D0")
    TSP.addConstrs(t[i] >= Nodes[i].TW[0] for i in Gnodes if i != "D1")
    # fix he tour start time
    TSP.addConstr(t["D0"] >= start_time)

    TSP.update()
    TSP.write("TSP_Model.mps")
    # Optimize mode
    TSP.Params.OutputFlag=0
    #TSP.params.LazyConstraints = 1
    TSP.optimize()
    if TSP.status != 2:
        print("TSP is not feasible")
        return Gnodes
    solution = TSP.getAttr('x', x)
    selected = [(i,j) for i,j in x.keys() if solution[i,j] > 0.5]
    route = subtour(selected)
    if len(route) != n :
        print(Gnodes)
        print(route)
    return (route , TSP.Objval)