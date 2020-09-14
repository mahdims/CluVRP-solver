import numpy as np
import time
import copy
import sys
import itertools as it
from math import sqrt
from TSP_Solver import TSP_model


def Centroid(customers):
    if len(customers) == 1:
        reference = list(customers.values())[0].coord
    else:
        reference = sum([np.array(cust.coord) for cust in customers.values()]) / len(customers)
    return reference


def Gravity(customers):
    if len(customers) == 1:
        reference = list(customers.values())[0].coord
    else:
        reference = sum([cust.demand * np.array(cust.coord) for cust in customers.values()]) / len(customers)

    return reference


def Hamiltonian_cycle(Data, clu, TW_indicator=0):
    # note the hamiltonian cycle starts from the depot and end at the depot therefore we needs to add distances
    # Add the depot D0 and D1 to the distance matrix
    # calculate the hamiltonian cycle of the customers
    TSP_Nodes = copy.copy(clu.customers)
    TSP_Nodes["D0"] = Data["depot"]
    TSP_Nodes["D1"] = Data["depot"]
    time_start = time.time()
    if TW_indicator:
        # clu.HC_sequence, clu.HC_cost = TSPTW_model(Dis, Nodes=TSP_Nodes, start_time=0)
        pass
    else:
        clu.HC_sequence, clu.HC_cost = TSP_model(clu.Dis, Nodes=TSP_Nodes)

    if not clu.HC_sequence:
        sys.exit("Cluster %s is infeasible" % clu.ID)
    else:
        print("We find the Hamiltonian cycle for cluster %s in %s sec" % (clu.ID, round(time.time()-time_start,3)))
        clu.HC_sequence.remove("D0")
        clu.HC_sequence.remove("D1")
        clu.HC_cost = clu.HC_cost - clu.Dis[("D0", clu.HC_sequence[0])] - clu.Dis[(clu.HC_sequence[-1], "D1")]

    return int(clu.HC_cost + sum([cus.service_time for cus in clu.customers.values()]))


def Ref2Ref_inter_cluster(Data):
    Clusters_ID = list(Data["Clusters"].values()) + [Data["depot"]]
    clu_dis = {}
    for clu1, clu2 in it.combinations(Clusters_ID, 2):
        if clu1.ID == "D0":
            ref1 = clu1.coord
        else:
            ref1 = clu1.reference

        if clu2.ID == "D0":
            ref2 = clu2.coord
        else:
            ref2 = clu2.reference

        clu_dis[clu1.ID, clu2.ID] = sqrt((ref1[0]-ref2[0])**2 + (ref1[1]-ref2[1])**2)
    return clu_dis


def nearest_inter_cluster(Data):
    clu_dis = {}
    depot = end_points1 = end_points2 = []
    Clusters_ID = list(Data["Clusters"].values()) + [Data["depot"]]
    for clu1, clu2 in it.combinations(Clusters_ID, 2):
        if clu1.ID == "D0":
            end_points2 = clu2.trans_nodes[clu1.ID]
            intra_arc_list = [[(a, b), Data["Full_dis"][a, b]]
                              for a, b in it.product(["D0"], end_points2)]
        elif clu2.ID == "D0":
            end_points1 = clu1.trans_nodes[clu2.ID]
            intra_arc_list = [[(a, b), Data["Full_dis"][a, b]]
                              for a, b in it.product(["D0"], end_points1)]
        else:
            end_points1 = clu1.trans_nodes[clu2.ID]
            end_points2 = clu2.trans_nodes[clu1.ID]
            intra_arc_list = [[(a, b), Data["Full_dis"][a, b]]
                              for a, b in it.product(end_points1, end_points2)]

        min_arc, min_dis = min(intra_arc_list, key=lambda x: x[1])
        clu_dis[clu1.ID, clu2.ID] = min_dis

    return clu_dis


class aggregationScheme:
    def __init__(self, ref, cscost, cstime, inter, disAgg, entry_exit):
        if ref == "Centroid":
            self.reference_point = Centroid
        elif ref == "Gravity":
            self.reference_point = Gravity
        else:
            sys.exit("Invalid reference point option")

        if cscost == "LB":
            self.service_cost = None
        elif cscost == "UB":
            self.service_cost = None
        elif cscost == "Combine":
            self.service_cost = None
        elif cscost == "SHC":
            self.service_cost = Hamiltonian_cycle
        else:
            sys.exit("Invalid cluster service cost option")

        if cstime == "LB":
            self.service_time = None
        elif cstime == "UB":
            self.service_time = None
        elif cstime == "Combine":
            self.service_time = None
        elif cstime == "SHC":
            self.service_time = Hamiltonian_cycle
        else:
            sys.exit("Invalid cluster service time option")

        if inter == "Nearest":
            self.inter_distance = nearest_inter_cluster
        elif inter == "Ref2Ref":
            self.inter_distance = Ref2Ref_inter_cluster
        else:
            sys.exit("Invalid inter clusters distance option")

        if disAgg == "OneTsp":
            self.dis_aggregation = None
        elif disAgg == "Sequential":
            self.dis_aggregation = None
        else:
            sys.exit("Invalid disaggregation option")

        if entry_exit == "Nearest":
            self.entry_exit = None
        elif entry_exit == "SHPs":
            self.entry_exit = None
        else:
            sys.exit("Invalid entry exit option")


def aggregation_pars(Data, Scheme):
    # This calculates the aggregated parameters , cluster demand, cluster service time and cost
    for clu in Data["Clusters"].values():
        clu.demand = sum([cus.demand for cus in clu.customers.values()])
        clu.reference = Scheme.reference_point(clu.customers)
        clu.service_time = Scheme.service_time(Data, clu,)
        clu.service_cost = Scheme.service_time(Data, clu,)
    return Data


def aggregation(Data, Scheme):
    # Cluster parameters
    Data = aggregation_pars(Data, Scheme)
    # Calculate teh distance between clusters
    clu_dis = Scheme.inter_distance(Data)

    return Data, clu_dis
