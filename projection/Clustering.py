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


def draw_the_honeycomb(clusters, X_range=(0,120), Y_range= (0,120)):
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

from Hexogonal import Hexo

def Honeycomb_Clustering(Data):
    # This function just create the clusters, find which customers are inside the clusters and only
    # keep the clusters with customers inside
    # The important factor of Region size (Hexagonal size) is "r"
    TW_indicator = 0
    Co = 0.8660254037844386
    # radius
    r = 80
    d = r * Co
    # maximum y or x in 2_D map
    X_range = Data["X_range"]
    Y_range = Data["X_range"]
    count = 1
    # Creating the clusters centers
    for inx, x in enumerate(np.arange(X_range[0], X_range[1] + r, 1.5 * r)):
        inx += 1
        position = "F" # the cluster in the first row
        indic = inx - int(inx / 2) * 2 == 0
        for y in np.arange(Y_range[0] + indic * d, Y_range[1]+r, 2 * d):
            if (y + 2*d) >= Y_range[1]+r:
                position = "L" # cluster is in the last row
            # Defining the clusters object
            new_hex = Hexo((x, y), r)
            # Find and update the cluster neighbors (it is just needed for re-clustering algorithm)
            # Data, new_hex = find_neighbors(Data, d, new_hex, count, indic, position)
            Data["Clusters"][count] = new_hex
            count += 1
            position = "M" # cluster is in the middle rows

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
            # Assign the clusters ID
            clu.ID = "Cu" + str(ID_cont)
            ID_cont += 1
            ID_translation[key] = clu.ID
            # Calculate the Time distance among the customers in a cluster
            # clu.initial_T_dis_matrix(Data)
            used_clusters.append((clu.ID, clu))
        else:
            ID_translation[key] = []

    used_clusters = dict(used_clusters)
    # Change the neighbours ID
    used_clusters = Change_neighbours_names(used_clusters, ID_translation)
    # change the clusters according to the time windows suitabilities
    # Redefined_clusters = redefine_the_clusters(Data, used_clusters)
    # draw_the_honeycomb(Redefined_clusters, X_range, Y_range)
    for clu in used_clusters.values():
        # Assign the cluster name to customers
        for cus in clu.customers.values():
            cus.clu_id = clu.ID
        # create the cluster distance matrix (for inside clusters)
        clu.cluster_dis_matrix(Data)
        # create the transition set for each cluster
        clu.Create_transSet(Data["Full_dis"], used_clusters)

    Data["Clusters"] = used_clusters

    return Data


'''
def K_means_Clustering(Data):
    customers_x = Data["Cx"]
    customers_y = Data["Cy"]
    # create kmeans object
    N_of_clusters = 10
    kmeans = KMeans(n_clusters=N_of_clusters)
    # fit kmeans object to data
    kmeans.fit(zip(customers_x.values(),customers_y.values()))
    # save new clusters for chart
    y_km = kmeans.fit_predict(zip(customers_x.values(),customers_y.values()))

    for cl in range(N_of_clusters):
        Clu = 0
        Clu.K_mean_center =  kmeans.cluster_centers_[cl]
        Data["Clusters"].append(Clu)

    return Data
'''