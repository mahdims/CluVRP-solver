
from gurobipy import *
import networkx as nx
from itertools import *


## We are going to solve the VRP with 2 commodity flow formulation with we expect to have a very good performance for small and large size problems (not the normal size)
def Time_Calc(Dis,NN,R):
    Travelcost=0
    PreNode=0
    for n in R[1:-1]: # travel time calculation
        Travelcost +=  Dis[PreNode,n]
        PreNode=n
    return Travelcost
    
    
def routes_finder(X,N):
    routes=[]
    starters=[tub[1] for tub in X if tub[0]==0]
    for st in starters:

        X.remove((0,st))
        current_node=st
        route=[0,st]

        while current_node != N:
            for tub in X:
                if current_node in tub:
                    break

            X.remove( tub )
            next_node=list(set(tub)-set([current_node]))

            # this If is just temproray
            if next_node ==[0]:
                route += [N]
                starters.remove(current_node)
                break

            route += next_node
            current_node = next_node[0]
        routes.append(route)
    return routes


def VRP_Exact_solver(Node_demand, Dis, Q):
    Node_set = Node_demand.keys()
    N = max(Node_set)
    V_c = set(Node_set) - set([0,N])
    complement = [(i,j) for i,j in Dis.keys() if i<j]
    Travel_time = list(Dis.values() )
    BigM = sum(Travel_time) / 2
    Total_demand = sum([Node_demand[i] for i in V_c])
    ################ MODEL 2 ####################
    # Basic CVRP ,  know number of vehicles , without travel time limit or time windows
    CF_MIP=Model("Two_Commodity_Flow ")
    x=CF_MIP.addVars(complement,lb=0,ub=1,name="x",vtype = GRB.BINARY)
    y=CF_MIP.addVars(complement,name="y")
    w=CF_MIP.addVars(complement,name="w")
    M = CF_MIP.addVar(name="M",vtype = GRB.INTEGER)
    #u=CF_MIP.addVars(G.nodes,name="u")
    #v=CF_MIP.addVars(range(NN),name="v")#,vtype=GRB.INTEGER)

    CF_MIP.setObjective(quicksum(Dis[i,j]*x[i,j] for i,j in x.keys()))
    CF_MIP.addConstrs(quicksum(w[i,j]-y[i,j] for j in Node_set if j > i) +
                      quicksum(-w[j,i]+y[j,i] for j in Node_set if j < i) == 2*Node_demand[i] for i in V_c)
    CF_MIP.addConstr(quicksum(y.select(0,'*')) == Total_demand)
    CF_MIP.addConstr(quicksum(w.select(0,'*')) == M*Q-Total_demand )
    CF_MIP.addConstr(quicksum(w.select('*',N)) == M*Q)
    CF_MIP.addConstrs(y[i,j]+w[i,j] == Q*x[i,j] for i,j in x.keys())
    #CF_MIP.addConstrs(u[j]>=u[i]+Dis[i,j]+BigM*(x[i,j]-1) for i,j in complement)
    #CF_MIP.addConstrs(u[i]<=Data.Maxtour for i in Gc.nodes )
    CF_MIP.addConstrs(quicksum(x[i,j] for j in Node_set if j > i) + quicksum(x[j,i] for j in Node_set if j< i) == 2 for i in V_c)

    #CF_MIP.Params.OutputFlag = 0
    #CF_MIP.write("IPmodel.lp")
    CF_MIP.params.TimeLimit = 100
    CF_MIP.params.MIPGap = 0.0001
    CF_MIP.optimize()
    
    Objval = -1000000
    if CF_MIP.status != 3:
        Xv=CF_MIP.getAttr('x',x)
        Yv=CF_MIP.getAttr('x',y)
        Wv=CF_MIP.getAttr('x',w)

        Tours=[b[0] for b in Xv.items() if b[1] > 0.5]

        Tours=routes_finder(Tours, N)
        test= []
        for t in Tours:
            test += t
            Tour_demand=0
            for node in t:
                Tour_demand += Node_demand[node]
            if Tour_demand >= Q:
                print("The tour demand is more than Q by %f" %(Tour_demand-Q))
        test = list(set(test))
        test.sort()
        if list(Node_set) != test:
            print("found the mistake : not all nodes covered by vehicles")
            print(set(Node_set) - set(test))
        #VisitTime=[]
        #for tour in Tours:
        #    VisitTime.append([])
        #    for n in tour[:-1]:
        #        VisitTime[-1].append(round(Uv[n],1))
            #print(tour)
            #print("The Tour length is : %s \n" %round(Time_Calc(Dis,NN,tour),1) )
        #print(Yv)
    #return (CF_MIP.objVal,CF_MIP.ObjBound ,CF_MIP.Runtime,  CF_MIP.MIPGap)
    return (CF_MIP.objVal ,  Tours)