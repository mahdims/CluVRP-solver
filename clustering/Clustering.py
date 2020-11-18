import copy
import matplotlib.pyplot as plt
import numpy as np
import math
# from Redefine_the_clusters import redefine_the_clusters


def Calculate_time_distance(Data, Cust1, Cust2):
    dis = Data["Full_dis"]

    def one_way(cus1, cus2):
        k1 = 1 # benefit from being in the time windows
        k2 = 2 # lost of time because fo waiting
        k3 = 10 # penalty (time value) of not visiting a customer in the time window
        t_start = cus1.TW[0] + cus1.service_time + dis[(cus1.ID, cus2.ID)]
        t_end = cus1.TW[1] + cus1.service_time + dis[(cus1.ID, cus2.ID)]
        first_int = ( min(t_start, cus2.TW[0]), min(t_end,cus2.TW[0]) )
        second_int = ( min(max(cus2.TW[0] , t_start), cus2.TW[1]) , max(min(cus2.TW[1], t_end),cus2.TW[0]) )
        third_int = ( max(cus2.TW[1], t_start), max(cus2.TW[1], t_end) )

        distance = k2*(first_int[1]**2 - first_int[0]**2)/2 + (k1*cus2.TW[1]-(k1+k2)*cus2.TW[0]) * (first_int[1] - first_int[0])+\
            -k1*(second_int[1]**2 - second_int[0]**2)/2 + k1*cus2.TW[1] * (second_int[1] - second_int[0]) + \
            -k3 * (third_int[1] ** 2 - third_int[0] ** 2) / 2 + k3 * cus2.TW[1] * (third_int[1] - third_int[0])

        return round(distance / (t_end - t_start), 1)

    return max(one_way(Cust1, Cust2), one_way(Cust2, Cust1))


def Change_neighbours_names(clusters, Trans_dict):
    # Change the cluster ID in neighbourhoods
    for clu in clusters.values():
        temp = copy.copy(clu.neighbours)
        for nei in temp:
            if Trans_dict[nei]:
                inx = clu.neighbours.index(nei)
                clu.neighbours[inx] = Trans_dict[nei]
            else:
                clu.neighbours.remove(nei)

    return clusters


def find_neighbors(Data, d,new_hex, count, indic, position):
    X_range = Data["X_range"]
    # Number of hexagonal in one column
    Clu_in_col_min = math.ceil((X_range[1] - X_range[0] - d) / (2 * d))
    new_neighbours = []
    # find the Horizontal neighbors
    if position == "F":
        # The vertical neighbours
        new_neighbours += [count - Clu_in_col_min]
        if indic:
            new_neighbours += [count - Clu_in_col_min - 1]
    elif position == "L":
        # The horizontal neighbours
        new_neighbours += [count - 1]
        # The vertical neighbours
        new_neighbours += [count - Clu_in_col_min - 1]
        if indic:
            new_neighbours += [count - Clu_in_col_min]
    else:
        # The horizontal neighbours
        new_neighbours += [count - 1]
        # The vertical neighbours
        new_neighbours += [count - Clu_in_col_min - 1, count - Clu_in_col_min]

    for nei in new_neighbours:
        if nei in Data["Clusters"].keys():
            Data["Clusters"][nei].neighbours += [count]
            new_hex.neighbours += [nei]

    return Data, new_hex


def cluster_analysis(Data, clusters):
    N_cus= []
    Clu_demand = []
    for clu in clusters.values():
        N_cus.append(len(clu.customers))
        Clu_demand.append(clu.demand)
    print(f"{len(clusters)} ({min(N_cus)} {max(N_cus)} {round(float(sum(N_cus))/len(N_cus), 2)}) "
          f"({min(Clu_demand)} {max(Clu_demand)} {round(float(sum(Clu_demand))/len(Clu_demand),2)})")

    draw_the_honeycomb(Data, clusters)
    exit()

def draw_the_honeycomb(Data, clusters):
    X_range = Data["X_range"]
    Y_range = Data["Y_range"]
    # This function is just for tests
    # It will draw the honeycomb stracture with clusters numbers
    fig, ax = plt.subplots(1)
    ax.set_aspect('equal')
    ax.axis([*X_range, *Y_range])
    for key, cluster in clusters.items():
        ax.add_patch(cluster.Drawing())
        cus_coord = np.array([cus.coord for cus in cluster.customers.values()])
        ax.scatter(cus_coord[:, 0], cus_coord[:, 1])
        ax.text(*cluster.org, s=key, fontsize=12)
    plt.show()


from clustering import Hexogonal

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


def Honeycomb_Clustering(Data):
    # The important factor of Region size (Hexagonal size) is "r"
    # The cluster demand should be less than 0.3 0.4 0.5 presentage of the vehicle capacity
    # If the demand variation is low then decrease the cluster size, if the variation is high and there is
    # some clusters with only one customers and some with a lot more customers in the dense areas.
    # Then you should assign the far customers to the nearest clusters in the center.
    max_r = 100 # radius
    min_r = 5
    r = 80
    flag, clusters, ID_trans = create_the_clusters(Data, r)
    '''
    while max_r-min_r > 0.2:
        r = float(max_r + min_r) / 2
        print(r)
        flag, clusters, ID_trans = create_the_clusters(Data, r)
        if flag:
            min_r = r
        else:
            max_r = r

    '''

    # cluster_analysis(Data, clusters)
    # Change the neighbours ID
    clusters = Change_neighbours_names(clusters, ID_trans)
    # change the clusters according to the time windows suitabilities
    # Redefined_clusters = redefine_the_clusters(Data, used_clusters)
    # draw_the_honeycomb(Redefined_clusters, X_range, Y_range)
    for clu in clusters.values():
        # Assign the cluster name to customers
        for cus in clu.customers.values():
            cus.clu_id = clu.ID
        # create the cluster distance matrix (for inside clusters)
        clu.cluster_dis_matrix(Data["Full_dis"])
        # create the transition set for each cluster
        clu.Create_transSet(Data["Full_dis"], clusters)

    Data["Clusters"] = clusters

    return Data
