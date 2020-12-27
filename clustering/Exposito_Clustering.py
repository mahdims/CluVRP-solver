import numpy as np


def nearest_cus(Dist, list1, list2):
    new_dist = {}
    for cus1 in list1:
        for cus2 in list2:
            new_dist[(cus1, cus2)] = Dist[cus1, cus2]

    edge, min_edge = min(new_dist.items(), key=lambda x: x[1])

    return edge


def Exposito_Clustering(Data, percentage=0.3333):

    alpha = percentage * Data["C"]
    unassigned_cus = list(Data["Customers"].keys())
    assigned_cus = ["D0"]
    clusters = {"Cu0": Data["depot"]}
    N = len(Data["Customers"])
    counter = 0
    while len(assigned_cus) < N+1:
        if len(assigned_cus) == 1:
            start_cus = np.random.choice(unassigned_cus)
        else:
            in_list1, start_cus = nearest_cus(Data["Full_dis"], assigned_cus, unassigned_cus)

        new_clu = [start_cus]
        counter += 1
        assigned_cus.append(start_cus)
        unassigned_cus.remove(start_cus)
        Ccap = Data["Customers"][start_cus].demand

        while Ccap < alpha and len(assigned_cus) < N+1 :
            candidate_cus = [cus for cus in unassigned_cus if Data["Customers"][cus].demand + Ccap <= alpha]
            _, cus_to_add = nearest_cus(Data["Full_dis"], assigned_cus, candidate_cus)
            new_clu.append(cus_to_add)
            assigned_cus.append(cus_to_add)
            unassigned_cus.remove(cus_to_add)
            Ccap += Data["Customers"][cus_to_add].demand

        clusters = clusters | {f"Cu{counter}": new_clu}

    return clusters
