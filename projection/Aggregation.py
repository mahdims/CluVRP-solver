import numpy as np
import time
import copy
import sys
import itertools as it
from math import sqrt
from read import Customer
from TSP_Solver import TSP_model, TSP_concorde


def euclidean_dis(A,B):
    return sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


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


def LU_service_cost(Data, clu):

    if len(clu.customers) == 1:
        return list(clu.customers.values())[0].service_time
    elif len(clu.customers) == 2:

        return clu.Dis[tuple(list(clu.customers.keys()))] +sum([cus.service_time for cus in clu.customers.values()])
    transSet = []
    for a in clu.trans_nodes.values():
        transSet += a
    transSet = list(set(transSet))

    Hamiltonian_paths = {}
    for cus1, cus2 in it.combinations(transSet, 2):
        distance = copy.copy(clu.Dis)
        # Create the distance matrix
        for n in set(clu.customers.keys()) - set([cus1, cus2]):
                distance["D0", n] = distance[cus1, n]
                distance[n, "D0"] = distance["D0", n]
                del distance[cus1, n], distance[n, cus1]
                distance[n, "D1"] = distance[n, cus2]
                distance["D1", n] = distance[n, "D1"]
                del distance[n, cus2], distance[cus2, n]
        for n,m in it.combinations([cus1, cus2, "D0", "D1"],2):
            try:
                del distance[n, m], distance[m, n]
            except KeyError:
                pass
        nodeSet = copy.copy(clu.customers)
        nodeSet["D0"] = nodeSet[cus1]
        nodeSet["D1"] = nodeSet[cus2]
        del nodeSet[cus1], nodeSet[cus2]
        HP, HP_cost = TSP_model(distance, Nodes=nodeSet)
        HP[0] = cus1
        HP[-1] = cus2
        Hamiltonian_paths[(cus1, cus2)] = [HP_cost, HP]
    MinHp, (Min_cost, Seq) = min(Hamiltonian_paths.items(), key=lambda x: x[1][0])

    return int(Min_cost + sum([cus.service_time for cus in clu.customers.values()]))


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
        # clu.HC_sequence, clu.HC_cost = TSP_model(clu.Dis, Nodes=TSP_Nodes)
        clu.HC_sequence, clu.HC_cost = TSP_concorde(clu.Dis, TSP_Nodes)

    if not clu.HC_sequence:
        sys.exit("Cluster %s is infeasible" % clu.ID)
    else:
        # print("We find the Hamiltonian cycle for cluster %s in %s sec" % (clu.ID, round(time.time()-time_start,3)))
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
        clu_dis[clu2.ID, clu1.ID] = clu_dis[clu1.ID, clu2.ID]
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
        clu_dis[clu2.ID, clu1.ID] = clu_dis[clu1.ID, clu2.ID]

    return clu_dis


def DisAgg_HC(Data, M_path, TW_indicator=0):
    BigM = 10 * max(Data["Full_dis"].values())
    Clusters = Data["Clusters"]
    Nodes_pool = {}
    Dis = {}
    # Build the node pool
    for inx, clu_ID in enumerate(M_path[:-1]):
        # The first node should be the depot
        if clu_ID == "D0":
            Nodes_pool[clu_ID] = Data["depot"]
            continue
        Clu = Clusters[clu_ID]
        Nodes_pool.update({cus_id: cus for cus_id, cus in Clu.customers.items()})
    # last customer should be depot as well
    Nodes_pool["D1"] = Data["Aux_depot"]
    # Build the distance matrix
    for node1, node2 in it.combinations(Nodes_pool.values(), 2):
        Dis[node1.ID, node2.ID] = Data["Full_dis"][node1.ID, node2.ID] + BigM * (node1.clu_id != node2.clu_id)
        Dis[node2.ID, node1.ID] = Dis[node1.ID, node2.ID]


    Sequence, Total_Cost = TSP_model(Dis, Nodes=Nodes_pool)
    return Sequence, Total_Cost - BigM * (len(M_path) - 1)


def DisAgg_Sequential(Data, M_path, TW_indicator=0):
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
            next_node = Customer("D1", Clusters[M_path[inx+1]].reference, 0, Data["depot"].TW, 0)

        # update the distance matrix to include the last and next node
        for n, cus in Clu.customers.items():
            Dis[last_node.ID, n] = Data["Full_dis"][(last_node_ID, cus.ID)]
            if M_path[inx + 1] == "D0":
                Dis[n, next_node.ID] = Data["Full_dis"][("D0", cus.ID)]
            else:
                Dis[n, next_node.ID] = euclidean_dis(cus.coord, next_node.coord)

        # solve the TSP  to find the hamiltonian path
        Nodes = copy.copy(Clu.customers)
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


class aggregationScheme:
    def __init__(self, ref, cscost, cstime, inter, disAgg, entry_exit):
        if ref == "Centroid":
            self.reference_point = Centroid
        elif ref == "Gravity":
            self.reference_point = Gravity
        else:
            sys.exit("Invalid reference point option. \n Options: Centroid , Gravity")

        if cscost == "LB":
            self.service_cost = LU_service_cost
        elif cscost == "UB":
            self.service_cost = None
        elif cscost == "Combine":
            self.service_cost = None
        elif cscost == "SHC":
            self.service_cost = Hamiltonian_cycle
        else:
            sys.exit("Invalid cluster service cost option. \n Options: LB, UB, Combine, SHC")

        if cstime == "LB":
            self.service_time = LU_service_cost
        elif cstime == "UB":
            self.service_time = None
        elif cstime == "Combine":
            self.service_time = None
        elif cstime == "SHC":
            self.service_time = Hamiltonian_cycle
        else:
            sys.exit("Invalid cluster service time option. \n Options: LB, UB, Combine, SHC")

        if inter == "Nearest":
            self.inter_distance = nearest_inter_cluster
        elif inter == "Ref2Ref":
            self.inter_distance = Ref2Ref_inter_cluster
        else:
            sys.exit("Invalid inter clusters distance option. Options: Nearest, Ref2Ref")

        if disAgg == "OneTsp":
            self.dis_aggregation = DisAgg_HC
        elif disAgg == "Sequential":
            self.dis_aggregation = DisAgg_Sequential
        else:
            sys.exit("Invalid disaggregation option. \n Options: OneTsp, Sequential")

        if entry_exit == "Nearest":
            self.entry_exit = "Nearest"
        elif entry_exit == "SHPs":
            self.entry_exit = "SHPs"
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
