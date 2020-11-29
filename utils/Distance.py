import itertools as it
import math


def euclidean_dis(A, B):
    return round(math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2))


def build_distance_matrix(depot, customers):
    distance = {}
    for cust1, cust2 in it.combinations(customers.values(), 2):
        distance[cust1.ID, cust2.ID] = euclidean_dis(cust1.coord, cust2.coord)
        distance[cust2.ID, cust1.ID] = distance[cust1.ID, cust2.ID]
    for a in customers.values():
        distance[("D0", a.ID)] = euclidean_dis(depot.coord, a.coord)
        distance[(a.ID, "D1")] = distance[("D0", a.ID)]
    distance[("D0", "D1")] = distance[("D1", "D0")] = 0
    return distance