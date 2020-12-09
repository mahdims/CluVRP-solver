from gurobipy import *
import networkx as nx
from itertools import *
# We are going to solve the VRP with 2 commodity flow formulation
# we expect to have a very good performance for small and large size problems (not the normal size)


def Time_Calc(Dis, NN, R):
    Travelcost = 0
    PreNode = 0
    for n in R[1:-1]: # travel time calculation
        Travelcost += Dis[PreNode, n]
        PreNode = n
    return Travelcost


def routes_finder(X, N):
    routes = []
    starters = [tub[1] for tub in X if tub[0] == "D0"]
    for st in starters:
        X.remove(("D0", st))
        current_node = st
        route = ["D0", st]

        while current_node != "D0":
            for tub in X:
                if current_node in tub:
                    break

            X.remove(tub)
            next_node = list(set(tub)-set([current_node]))

            # this If is just temproray
            if next_node == ["D0"]:
                route += ["D0"]
                # starters.remove(current_node)
                break

            route += next_node
            current_node = next_node[0]
        routes.append(route)
    return routes


def VRP_Model_2CF(Data, Dis):
    V_c = [a.re for a in Data["Clusters"].keys()]
    N = len(V_c)
    Node_set = V_c + ["D0"]
    complement = [(i, j) for i, j in Dis.keys() if i < j]
    Travel_time = list(Dis.values())
    BigM = sum(Travel_time) / 2
    Demand = {id: Data["Clusters"][id].demand for id in V_c}
    Demand["D0"] = 0
    ################ MODEL 2 ####################
    # Basic CVRP ,  know number of vehicles , without travel time limit or time windows
    CF_MIP = Model("Two_Commodity_Flow ")
    x = CF_MIP.addVars(complement, lb=0, ub=1, name="x", vtype=GRB.BINARY)
    y = CF_MIP.addVars(complement, name="y")
    w = CF_MIP.addVars(complement, name="w")
    M = CF_MIP.addVar(name="M", vtype=GRB.INTEGER)

    CF_MIP.setObjective(quicksum(Dis[i, j]*x[i, j] for i, j in x.keys()))
    CF_MIP.addConstrs(quicksum(w[i, j]-y[i, j] for j in Node_set if j > i) +
                      quicksum(-w[j, i]+y[j, i] for j in Node_set if j < i) == 2*Demand[i] for i in V_c)
    CF_MIP.addConstr(quicksum(y.select("D0", '*')) == sum(Demand.values()))
    CF_MIP.addConstr(quicksum(w.select("D0", '*')) == M*Data["C"]-sum(Demand.values()))
    CF_MIP.addConstr(quicksum(w.select('*', "D0")) == M*Data["C"])
    CF_MIP.addConstrs(y[i, j]+w[i, j] == Data["C"]*x[i, j] for i, j in x.keys())
    CF_MIP.addConstrs(quicksum(x[i, j] for j in Node_set if j > i)
                      + quicksum(x[j, i] for j in Node_set if j < i) == 2 for i in V_c)

    #CF_MIP.Params.OutputFlag = 0
    #CF_MIP.write("IPmodel.lp")
    CF_MIP.params.TimeLimit = 100
    CF_MIP.params.MIPGap = 0.0001
    CF_MIP.optimize()
    
    if CF_MIP.status != 3:
        Xv = CF_MIP.getAttr('x', x)
        Tours = [b[0] for b in Xv.items() if b[1] > 0.5]
        Tours = routes_finder(Tours, N)
        test = []
        for t in Tours:
            test += t
            Tour_demand=0
            for node in t:
                Tour_demand += Demand[node]
            if Tour_demand >= Data["C"]:
                print("The tour demand is more than Q by %f" %(Tour_demand-Q))
        test = list(set(test))
        test.sort()
        if list(Node_set) != test:
            print("found the mistake : not all nodes covered by vehicles")
            print(set(Node_set) - set(test))

    return CF_MIP.objVal,  Tours


def VRP_Model_SC(Data, Dis):
    V_c = list(Data["Clusters"].keys())
    N = len(V_c)
    Node_set = V_c + ["D0"]
    complement = [(i, j) for i, j in Dis.keys() if i != j]
    Travel_time = list(Dis.values())
    Demand = {id: Data["Clusters"][id].demand for id in V_c}
    Demand["D0"] = 0
    Service_time = {id: Data["Clusters"][id].service_time for id in V_c}
    Service_time["D0"] = 0
    ################ MODEL 3 ####################
    # Basic CVRP ,  know number of vehicles , without travel time limit or time windows
    SF_MIP = Model("Single_Commodity_Flow ")
    x = SF_MIP.addVars(complement, lb=0, ub=1, name="x", vtype=GRB.BINARY)
    f = SF_MIP.addVars(complement, lb=0, name="f")

    SF_MIP.setObjective(quicksum((Dis[i, j] + Service_time[i]) * x[i, j] for i, j in x.keys()))
    SF_MIP.addConstrs(quicksum(x.select(i, '*')) == 1 for i in V_c)
    SF_MIP.addConstrs(quicksum(x.select('*',i)) == 1 for i in V_c)
    SF_MIP.addConstrs(quicksum(f.select('*', i)) - quicksum(f.select(i, '*')) == Data["Clusters"][i].demand for i in V_c)
    SF_MIP.addConstrs(f[i,j] >= Demand[j] * x[i, j] for i, j in x.keys())
    SF_MIP.addConstrs(f[i, j] <= (Data["C"] - Demand[i]) * x[i, j] for i, j in x.keys())

    # SF_MIP.Params.OutputFlag = 0
    # SF_MIP.write("IPmodel.lp")
    SF_MIP.params.TimeLimit = 150
    SF_MIP.params.MIPGap = 0.001
    SF_MIP.optimize()

    if SF_MIP.status != 3:
        Xv = SF_MIP.getAttr('x', x)
        Fv = SF_MIP.getAttr('x', f)
        Tours = [b[0] for b in Xv.items() if b[1] > 0.5]

        Tours = routes_finder(Tours, N)
        test = []
        for t in Tours:
            test += t
            Tour_demand = 0
            for node in t:
                Tour_demand += Demand[node]
            if Tour_demand >= Data["C"]:
                print("The tour demand is more than Q by %f" %(Tour_demand-Data["C"]))

        print(set(Node_set) - set(test))
        # VisitTime=[]
        # for tour in Tours:
        #    VisitTime.append([])
        #    for n in tour[:-1]:
        #        VisitTime[-1].append(round(Uv[n],1))
        # print(tour)
        # print("The Tour length is : %s \n" %round(Time_Calc(Dis,NN,tour),1) )
        # print(Yv)
    # return (CF_MIP.objVal,CF_MIP.ObjBound ,CF_MIP.Runtime,  CF_MIP.MIPGap)
    return SF_MIP.objVal, Tours