import math
import itertools as it
from VRP_Solver import VRP_Exact_solver
from Model_VRP_SC import VRP_Exact_solver_SC


def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


def Direct_VRP(Data):
    # Calculate the distance matrix
    Dis = {}
    Node_demand = {}
    N = max( Data["C_coord"].keys())
    for node_1,node_2 in it.combinations(Data["C_coord"].keys(),2):
        Dis[node_1,node_2] = euclidean_dis(Data["C_coord"][node_1],Data["C_coord"][node_2])
        Dis[node_2, node_1] = Dis[node_1,node_2]
    for node in Data["C_coord"].keys():
        Node_demand[node] = Data["Demand"][node]
        Dis[0,node] = euclidean_dis(Data["D_coord"],Data["C_coord"][node])
        Dis[node, N+1] = Dis[0,node]
    Node_demand[0] = 0
    Node_demand[N+1] = 0
    #Cost, Tours = VRP_Exact_solver(Node_demand, Dis, Data["Q"])
    Cost, Tours = VRP_Exact_solver_SC(Node_demand, Dis, Data["Q"])
    return Tours,Cost