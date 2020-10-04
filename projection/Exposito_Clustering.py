
import numpy as np
import random

def create_the_clusters(Data, r):
    Data["Clusters"] = {}
    # This function create the clusters, find which customers are inside the clusters and only
    # keep those clusters with customers inside
    Co = 0.8660254037844386
    # maximum y or x in 2_D map
    X_range = Data["X_range"]
    Y_range = Data["X_range"]
    d = r * Co
    count = 1
    flag = True
    for inx, x in enumerate(np.arange(X_range[0], X_range[1] + r, 1.5 * r)):
        inx += 1
        position = "F"  # the cluster in the first row
        indic = inx - int(inx / 2) * 2 == 0
        for y in np.arange(Y_range[0] + indic * d, Y_range[1] + r, 2 * d):
            if (y + 2 * d) >= Y_range[1] + r:
                position = "L"  # cluster is in the last row
            # Defining the clusters object
            new_hex = Hexo((x, y), r)
            # Find and update the cluster neighbors (it is just needed for re-clustering algorithm)
            # Data, new_hex = find_neighbors(Data, d, new_hex, count, indic, position)
            Data["Clusters"][count] = new_hex
            count += 1
            position = "M"  # cluster is in the middle rows

    # Find which customer is inside which cluster
    for cus in Data["Customers"].values():
        for Clu in Data["Clusters"].values():
            if Clu.Check_if_inside(cus.coord):
                Clu.add_customer(cus)
                break

    # Find and keep the clusters that have customer inside
    ID_cont = 1
    used_clusters = []
    ID_translation = {}
    for key, clu in Data["Clusters"].items():
        if clu.customers:
            clu.demand = sum([cus.demand for cus in clu.customers.values()])
            flag = flag and clu.demand <= Data["C"]
            # assert sum([cus.demand for cus in clu.customers.values()]) <= Data["C"]
            # Assign the clusters ID
            clu.ID = "Cu" + str(ID_cont)
            ID_cont += 1
            ID_translation[key] = clu.ID
            # Calculate the Time distance among the customers in a cluster
            # clu.initial_T_dis_matrix(Data)
            used_clusters.append((clu.ID, clu))
        else:
            ID_translation[key] = []

    return flag, dict(used_clusters), ID_translation


def nearest_cus(Dist, list1, list2):
    new_dist = {}
    BigM = max(Dist.values())
    for cus1 in list1:
        for cus2 in list2:
            new_dist[(cus1, cus2)] = Dist[cus1, cus2]

    edge, min_edge = min(new_dist.items(), key=lambda x: ((x[0][0] in list1 and x[0][1] in list2) * BigM + 1) * x[1])

    return edge


def Exposito_Clustering(Data):
    percentage = 0.25
    alpha = percentage * Data["C"]
    unassigned_cus = list(Data["Customers"].keys())
    assigned_cus = ["D0"]
    clusters = {"Cu0": Data["depot"]}
    N = len(Data["Customers"])

    while len(assigned_cus) < N+1:
        if len(assigned_cus) == 1:
            current = np.random.randint(N)
        else:
            edge, _ = nearest_cus(Data["Full_dis"], unassigned_cus, assigned_cus)

        new_clu = [edge[0]]
        assigned_cus.append(edge[0])
        unassigned_cus.remove(edge[0])
        Ccap = 0

        while Ccap <= alpha:
            d = 0

    return