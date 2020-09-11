from gurobipy import *


def Time_Calc(Dis, NN, R):
    Travelcost = 0
    PreNode = 0
    for n in R[1:-1]:  # travel time calculation
        Travelcost += Dis[PreNode, n]
        PreNode = n
    return Travelcost


def routes_finder(X, N):
    routes = []
    starters = [tub[1] for tub in X if tub[0] == 0]
    for st in starters:
        X.remove((0, st))
        current_node = st
        route = [0, st]

        while current_node != 0:
            for tub in X:
                if current_node in tub:
                    break

            X.remove(tub)
            next_node = list(set(tub) - set([current_node]))
            route += next_node

            current_node = next_node[0]
        routes.append(route)
    return routes


def VRP_Exact_solver_SC(Node_demand, Dis, Q):
    Node_set = Node_demand.keys()
    N = max(Node_set)
    V_c = set(Node_set) - set([0, N])
    Node_set = set(Node_set) - set([N])
    for n in V_c:
        Dis[n,0] = Dis[0,n]
        del Dis[n,N]
    complement = [(i, j) for i, j in Dis.keys() if i != j]
    Travel_time = list(Dis.values())
    BigM = sum(Travel_time) / 2
    Total_demand = sum([Node_demand[i] for i in V_c])
    ################ MODEL 3 ####################
    # Basic CVRP ,  know number of vehicles , without travel time limit or time windows
    SF_MIP = Model("Single_Commodity_Flow ")
    x = SF_MIP.addVars(complement, lb=0, ub=1, name="x", vtype=GRB.BINARY)
    f = SF_MIP.addVars(complement, lb=0,name="f")

    SF_MIP.setObjective(quicksum(Dis[i, j] * x[i, j] for i, j in x.keys()))
    SF_MIP.addConstrs(quicksum(x.select(i, '*')) == 1 for i in V_c)
    SF_MIP.addConstrs(quicksum(x.select('*',i)) == 1 for i in V_c)
    SF_MIP.addConstrs(quicksum(f[j,i] for j in Node_set if i != j) + Node_demand[i] == quicksum(f.select(i,'*')) for i in V_c)
    SF_MIP.addConstrs(f[i,j] >= Node_demand[i] * x[i, j] for i, j in x.keys())
    SF_MIP.addConstrs(f[i, j] <= (Q - Node_demand[i]) * x[i, j] for i, j in x.keys())

    # SF_MIP.Params.OutputFlag = 0
    # SF_MIP.write("IPmodel.lp")
    SF_MIP.params.TimeLimit = 100
    SF_MIP.params.MIPGap = 0.00001
    SF_MIP.optimize()

    Objval = -1000000
    if SF_MIP.status != 3:
        Xv = SF_MIP.getAttr('x', x)
        Fv = SF_MIP.getAttr('x', f)
        Tours = [b[0] for b in Xv.items() if b[1] > 0.5]

        Tours = routes_finder(Tours, N)
        test = []
        for t in Tours:
            test += t
            Tour_demand= 0
            for node in t:
                Tour_demand +=Node_demand[node]
            if Tour_demand >= Q:
                print("The tour demand is more than Q by %f" %(Tour_demand-Q))
        test = list(set(test))
        test.sort()
        if list(Node_set) != test:
            print("found the mistake : not all nodes covered by vehicles")
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
    return (SF_MIP.objVal, Tours)