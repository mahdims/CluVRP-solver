import math
import os
import copy
from TSP_Solver import TSP_model
from read import Customer
# How to find the actual sequence fo the nodes after knowing the cluster ones.
# 1- calculate the Hamiltonian path from last node of previous cluster to the center of the next on.(shouldn't be that slow)
# 1.1 - connect the hamiltonion cycles of two clusters where there is the minimum distance of two nodes.(super fast)
# 3- just solve a TSP for each vehicle we shouldn't respect the clusters bounds anymore (time consuming)
# 4- in case we have more information form aggregation like 3-D matrix with hamiltonion paths we can use that and approximate
#   or calculate the optimal node sequence. (fast)
# 5- Having the hamiltonion path between each pair of entering-exiting nodes , we can find the shortest path from depot to depot passing such pair of nodes
# for each cluster. for this refer to T. Vital 2015 page 5  (Hybrid metaheuristics for the Clustered Vehicle Routing Problem) or Pop et al.

def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)

## This the first option ###
def Dis_aggregation1(Data, M_path):
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
        if "D0" in Nodes.keys() or  "D1" in Nodes.keys():
            os.exit("The depot are in the customer set!!")
        Nodes[next_node.ID] = next_node
        Nodes[last_node.ID] = last_node
        Sequence, Current_time = TSP_model(Dis, Nodes, start_time)

        '''
        # Sequence Correction. Since we solve a TSP start and end of the Hamiltonion path should be adjusted
        inx_s = Sequence.index(last_node_ID)
        if inx_s == len(Sequence)-1: # when the start of the sequence is at the last position
            if Sequence[0] == next_node_ID: # easy the end is at the first just reverse every thing
                Sequence.reverse()
            if Sequence[inx_s-1] == next_node_ID: # 180 degree the opposite of what we need
                Sequence = Sequence[inx_s:] + Sequence[:inx_s]
        else:
            if Sequence[inx_s+1] == next_node_ID:
                inx_e = inx_s+1
                Sequence = Sequence[:inx_e][::-1] + Sequence[inx_e:][::-1]
            if Sequence[inx_s - 1] == next_node_ID:
                Sequence = Sequence[inx_s:] + Sequence[:inx_s]
        '''
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

        # Update the last node form the hamiltonian path
        last_node_ID = Sequence[-2]
        last_node = copy.copy(Data["Customers"][last_node_ID])
        last_node.ID = "D0"

        # update the start_time for the next cluster
        start_time = Current_time - last_node.service_time

    return real_path, Total_time