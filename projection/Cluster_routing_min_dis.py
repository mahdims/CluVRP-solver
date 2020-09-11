#import networkx as nx
import math
import itertools as it
from VRP_Solver import VRP_Exact_solver

def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)

def Intera_Clusters_dis(Clu_1,Clu_2):
    min_cost= 1000000
    if type(Clu_1).__name__ == "tuple":
        first_coord_list = [(0 ,Clu_1)]
    else:
        first_coord_list = Clu_1.customers_coord.items()

    for node_1_ID, node_1 in first_coord_list:
        for node_2_ID, node_2 in Clu_2.customers_coord.items():
            if euclidean_dis(node_1,node_2) < min_cost:
                min_cost = euclidean_dis(node_1,node_2)
                connecting_nodes = (node_1_ID,node_2_ID)

    if type(Clu_1).__name__ == "tuple":
        min_cost += Clu_2.HC_cost/2
    else:
        min_cost += Clu_1.HC_cost/2 + Clu_2.HC_cost/2

    return min_cost


def Cluster_routing_min_dis(Data):
    # this function will build the aggregated graph and calculate the minimum distance between nodes in a cluster
    # Then I will call the VRP solver to find the Master tour over clsuters
    Accupied_cluesters={}
    ag_dis={}
    Node_demand = {}
    N = 0
    # find the in used clusters and create the master graph nodes
    for clu in Data["Clusters"].values():
        if len(clu.centroid):
            Node_demand[clu.ID] = clu.demand
            #G.add_node(clu.ID, demand=clu.demand, Coords=clu.centroid)
            Accupied_cluesters[clu.ID] = clu
            if clu.ID >=N: # The maximum cluster ID
                N = clu.ID

    Node_demand[0] = 0
    Node_demand[N+1] = 0
    #G.add_node(0 , demand = 0 , Coords = Data["D_coord"])
    #G.add_node(N+1, demand=0, Coords=Data["D_coord"])
    # create the edges of the master graph and prepare the distance matrix of it
    for clu_i ,clu_j in it.combinations(Accupied_cluesters.values(),2) :
        ag_dis[(clu_i.ID,clu_j.ID)] = Intera_Clusters_dis(clu_i, clu_j)
        ag_dis[(clu_j.ID, clu_i.ID)] = ag_dis[(clu_i.ID,clu_j.ID)]
        #G.add_edge(clu_i.ID,clu_j.ID, weight = ag_dis[(clu_i.ID,clu_j.ID)])
    for clu_ID in Accupied_cluesters.keys():
        ag_dis[(0,clu_ID)] = Intera_Clusters_dis(Data["D_coord"], Accupied_cluesters[clu_ID])
        ag_dis[(clu_ID, N+1)] = ag_dis[(0,clu_ID)]
        #G.add_edge(0, clu_ID, weight=ag_dis[(0, clu_ID)])
        #G.add_edge(clu_ID, N+1, weight=ag_dis[(clu_ID, N+1)])
    # Call the VRP solver
    Cost,  Tours = VRP_Exact_solver(Node_demand,ag_dis,Data["Q"])
    return Tours
