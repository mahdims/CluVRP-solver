import math
import numpy as np
from TSP_Solver import TSP_model
import itertools as it

# How to find the actual sequence fo the nodes after knowing the cluster ones.
# 1- calculate the Hamiltonian path from last node of previous cluster to the center of the next on.(shouldn't be that slow)
# 1.1 - connect the hamiltonion cycles of two clusters where there is the minimum distance of two nodes.(super fast)
# 2- Update the cost of intera cluster arcs (add M) and solve a TSP for each vehicle route. (Most time consuming)
# 3- just solve a TSP for each vehicle why not ? why we should respect the clusters bounds anymore (again time consuming)
# 4- in case we have more information form aggregation like 3-D matrix with hamiltonion paths we can use that and approximate
#   or calculate the optimal node sequence. (fast)
# 5- Having the hamiltonion path between each pair of entering-exiting nodes , we can find the shortest path from depot to depot passing such pair of nodes
# for each cluster. for this refer to T. Vital 2015 page 5  (Hybrid metaheuristics for the Clustered Vehicle Routing Problem) or Pop et al.

def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)

### This the 3rd option ###
def Dis_aggregation2(Data, M_path):
    Aux_depot = Data["Axu_depot"]
    Depot_coord = Data["D_coord"]
    Clusters = Data["Clusters"]
    N = max(M_path)
    Nodes_pool = {}
    Dis={}
    for inx, clu_ID in enumerate(M_path):

        # The first last node should be the depot
        if clu_ID == 0:
            Nodes_pool.update({clu_ID:Depot_coord})
            continue
        if clu_ID == N:
            Nodes_pool.update({Aux_depot:Depot_coord})
            continue

        Clu = Clusters[clu_ID]
        Nodes_pool.update(Clu.customers_coord)
    # Build the distnce matrix
    for (node_1_ID,node_1), (node_2_ID,node_2) in it.combinations(Nodes_pool.items(), 2):
        Dis[node_1_ID,node_2_ID] = euclidean_dis(node_1, node_2)
        Dis[node_2_ID,node_1_ID] = Dis[node_1_ID,node_2_ID]


    Sequence, Total_Cost = TSP_model(Dis, Nodes=Nodes_pool.keys())
    last_node_ID = 0
    next_node_ID = Aux_depot
    # Sequence Correction. Since we solve a TSP start and end of the Hamiltonion path should be adjusted
    inx_s = np.where(np.array(Sequence) == last_node_ID)[0][0]
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


    return Sequence , Total_Cost