import math
import os
import sys
import copy
from TSP_Solver import TSP_model
from read import Customer
#from TSPTW_Solver import TSPTW_model


# How to find the actual sequence fo the nodes after knowing the cluster ones?
# We calculate the Hamiltonian path from last node of previous cluster to the center of the next on.


def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


def Dis_aggregation(Data, M_path, TW_indicator):
    Clusters = Data["Clusters"]
    N = max(M_path)
    start_time = 0
    real_path = []
    Total_time = 0
    last_node_ID = "D0"
    for inx, clu_ID in enumerate(M_path[:-1]):

        # The first last node should be the depot
        if clu_ID == "D0":
            last_node = copy.copy(Data["depot"])
            real_path.append(last_node.ID)
            continue

        Clu = Clusters[clu_ID]
        Dis = Clu.Dis

        # Next node
        if M_path[inx + 1] == "D0": # if we are at the last cluster
            next_node = copy.copy(Data["depot"])
            next_node.ID = "D1"
        else: # otherwise (if we are at a middle cluster)
            next_node = Customer("D1", Clusters[M_path[inx+1]].centroid, 0, Data["depot"].TW, 0)

        # update the distance matrix to include the last and next node
        if Data["Full_dis"]:
            for n, cus in Clu.customers.items():
                Dis[last_node.ID, n] = Data["Full_dis"][(cus.ID, last_node_ID)]
                if M_path[inx + 1] == "D0":
                    Dis[n, next_node.ID] = Data["Full_dis"][(cus.ID, "D0")]
                else:
                    Dis[n, next_node.ID] = euclidean_dis(cus.coord, next_node.coord)
        else:
            for n,cus in Clu.customers.items():
                Dis[last_node.ID, n] = euclidean_dis(cus.coord, last_node.coord)
                Dis[n, next_node.ID] = euclidean_dis(cus.coord, next_node.coord)

        # solve the TSP  to find the hamiltonian path
        Nodes = Clu.customers
        Nodes[next_node.ID] = next_node
        Nodes[last_node.ID] = last_node
        if TW_indicator:
            Sequence, Current_time = TSPTW_model(Dis, Nodes, start_time)
        else:
            Sequence, Current_time = TSP_model(Dis, Nodes)

        # Update the total time
        if M_path[inx + 1] == "D0":
            pass
        else:
            Current_time -= Dis[Sequence[-2], next_node.ID]
        Total_time += Current_time

        # Update the real (global) route
        if M_path[inx + 1] == "D0":
            real_path += Sequence[1:]
        else:
            real_path += Sequence[1:-1]

        if len(Sequence) == 0: # Extra check delete !
            sys.exit("The path became infeasible for cluster %s" %clu_ID)
        # Update the last node form the hamiltonian path
        last_node_ID = Sequence[-2]
        last_node = copy.copy(Data["Customers"][last_node_ID])
        last_node.ID = "D0"
        # update the start_time for the next cluster
        start_time = Current_time - last_node.service_time

    return real_path, Total_time
