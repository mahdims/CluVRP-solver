import numpy as np
import pickle
import copy
import sys
import itertools as it
from math import sqrt
from utils import read
from tsp_solver import TSP_Solver


def euclidean_dis(A, B):
    return sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


def Centroid(customers):
    if len(customers) == 1:
        reference = list(customers.values())[0].coord
    else:
        reference = sum([np.array(cust.coord) for cust in customers.values()]) / len(customers)
    return reference


def service_time(Data, clu,):

    return sum([Data["Customers"][cus].service_time for cus in clu.customers.keys()])


def nearest_cus(point, clu):
    # This function finds the nearest customer to the reference point of next or previous cluster
    min_dis = 1000000000000
    for cus in clu.customers.values():
        c_dis = euclidean_dis(point, cus.coord)
        if c_dis < min_dis:
            min_dis = c_dis
            near_cus = cus.ID

    # TODO find the nearest customer in the other cluster to calculate the distance correctly.
    return near_cus, min_dis


def inter_distance(Data):

    # Read the hamiltonian path data for the instance
    file_obj = open("./data/Clu/SHPs/%s" % Data["Instance_name"], 'rb')
    All_SHPs = pickle.load(file_obj)
    file_obj.close()
    # For each cluster select the
    clu_dis = {}
    for clu in Data["Clusters"].values():
        Clusters = set(list(Data["Clusters"].values()) + [Data["depot"]]) - set([clu])
        Hamiltonian_paths = All_SHPs[clu.ID]
        clu_dis[clu.ID] = {}
        if len(Hamiltonian_paths) == 1:
            key = list(Hamiltonian_paths.keys())[0]
            val = list(Hamiltonian_paths.values())[0]
            clu_dis[clu.ID]["E","E"] = (key, val)

    for clu1, clu2 in it.combinations(Clusters, 2):
        if clu1.ID == "D0":
            ref1 = clu1.coord
        if clu2.ID == "D0":
            ref2 = clu2.coord
        else:
            ref2 = clu2.reference
        start, pre_dis = nearest_cus(clu1.reference, clu)
        end, next_dis = nearest_cus(clu2.reference, clu)
        clu_dis[clu.ID][clu1.ID, clu2.ID] = [(start, end), pre_dis + Hamiltonian_paths[(start, end)]]
        clu_dis[clu.ID][clu2.ID, clu1.ID] = [(end, start), Hamiltonian_paths[(end, start)] + next_dis]
    return clu_dis


def dis_aggregation(Data, M_path, TW_indicator=0):
    Clusters = Data["Clusters"]
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
            next_node = read.Customer("D1", Clusters[M_path[inx+1]].reference, 0, Data["depot"].TW, 0)

        # update the distance matrix to include the last and next node
        for n, cus in Clu.customers.items():
            Dis[last_node.ID, n] = Data["Full_dis"][(last_node_ID, cus.ID)]
            Dis[n, last_node.ID] = Dis[last_node.ID, n]
            if M_path[inx + 1] == "D0":
                Dis[n, next_node.ID] = Data["Full_dis"][("D0", cus.ID)]
            else:
                Dis[n, next_node.ID] = euclidean_dis(cus.coord, next_node.coord)
                Dis[next_node.ID, n] = Dis[n, next_node.ID]

        Dis[last_node.ID, next_node.ID] = Dis[next_node.ID, last_node.ID] = - max(Dis.values())
        # solve the TSP  to find the hamiltonian path
        Nodes = copy.copy(Clu.customers)
        Nodes[next_node.ID] = next_node
        Nodes[last_node.ID] = last_node
        if TW_indicator:
            # Sequence, Current_time = TSPTW_model(Dis, Nodes, start_time)
            pass
        else:
            Sequence, Current_time = TSP_Solver.solve(Dis, Nodes, start=last_node.ID, end=next_node.ID)

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


def aggregation(Data):
    # Cluster parameters
    for clu in Data["Clusters"].values():
        clu.reference = Centroid(clu.customers)
        clu.service_time = service_time(Data, clu,)
        # clu.service_cost = service_time(Data, clu,)

    # Calculate the distance between clusters
    clu_dis = inter_distance(Data)

    return Data, clu_dis
