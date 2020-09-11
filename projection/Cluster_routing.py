import networkx as nx
import math
import itertools as it
from VRP_Solver import VRP_Exact_solver

def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)

def Cluster_routing(Data):
    # this function will build the aggregated graph and calculate the centriod distances
    # Then I will call the VRP solver to find the Master tour over clsuters
    Accupied_cluesters = {}
    ag_dis = {}
    G = nx.Graph() # obsulate exchanged with Node_demand
    Node_demand = {}
    N = 0
    # find the in used clusters and create the master graph nodes
    for clu in Data["Clusters"].values():
        if len(clu.centroid):
            Node_demand[clu.ID] = clu.demand
            # G.add_node(clu.ID, demand=clu.demand, Coords=clu.centroid)
            Accupied_cluesters[clu.ID] = clu
            if clu.ID >=N:
                N = clu.ID

    Node_demand[0] = 0
    Node_demand[N+1] = 0
    # G.add_node(0 , demand = 0 , Coords = Data["D_coord"])
    # G.add_node(N+1, demand=0, Coords=Data["D_coord"])
    # create the edges of the master graph and prepare the distance matrix of it
    for clu_i ,clu_j in it.combinations(Accupied_cluesters.values(),2) :
        ag_dis[(clu_i.ID,clu_j.ID)] = euclidean_dis(clu_i.centroid, clu_j.centroid)
        ag_dis[(clu_j.ID, clu_i.ID)] = ag_dis[(clu_i.ID,clu_j.ID)]
        # G.add_edge(clu_i.ID,clu_j.ID, weight = ag_dis[(clu_i.ID,clu_j.ID)])
    for clu_ID in Accupied_cluesters.keys():
        ag_dis[(0,clu_ID)] = euclidean_dis(Data["D_coord"] , Accupied_cluesters[clu_ID].centroid)
        ag_dis[(clu_ID, N+1)] = ag_dis[(0,clu_ID)]
        # G.add_edge(0, clu_ID, weight=ag_dis[(0, clu_ID)])
        # G.add_edge(clu_ID, N+1, weight=ag_dis[(clu_ID, N+1)])
    # Call the VRP solver
    Cost,  Tours = VRP_Exact_solver(Node_demand,ag_dis,Data["Q"])

    return Tours