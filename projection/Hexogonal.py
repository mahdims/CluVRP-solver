from math import sqrt, ceil
import itertools as it
import numpy as np
from matplotlib.patches import RegularPolygon


def euclidean_dis(A,B):
    return sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


def cluster_matrix(self, Full_dis):
    Dis = {}
    for a, b in it.combinations(self.customers.keys(), 2):
        if Full_dis:  # if the distance matrix is given
            Dis[(a, b)] = Full_dis[(a, b)]
            Dis[(b, a)] = Dis[(a, b)]
        else:  # if there is not distance matrix use the direct distances
            Dis[(a, b)] = euclidean_dis(self.customers[a].coord, self.customers[b].coord)
            Dis[(b, a)] = Dis[(a, b)]

    for cus in self.customers.values():
        Dis["D0", cus.ID] = Dis[cus.ID, "D0"] = Full_dis["D0", cus.ID]
        Dis[cus.ID, "D1"] = Dis["D1", cus.ID] = Dis["D0", cus.ID]
    # Store the distance matrix for all nodes in one cluster
    return Dis


def transSet(self, dis, clusters):
    transSet = {}
    N = ceil(len(self.customers) * Hexo.trans_percentage)
    for clu in clusters.values():
        if clu.ID != self.ID:
            cust_inx = it.product(list(self.customers.keys()), list(clu.customers.keys()))
            inter_dis = {key: dis[key] for key in cust_inx}
            inter_dis = sorted(inter_dis.items(), key=lambda x: x[1])
            transSet[clu.ID] = []
            while len(transSet[clu.ID]) < N:
                ((node, _), _) = inter_dis.pop(0)
                if node not in transSet[clu.ID]:
                    transSet[clu.ID].append(node)
    # find the nodes that connect this cluster to the depot
    cust_inx = it.product(["D0"],list(self.customers.keys()))
    inter_dis = {key: dis[key] for key in cust_inx}
    inter_dis = sorted(inter_dis.items(), key=lambda x: x[1])
    transSet["D0"] = [node for (_, node), _ in inter_dis[:N]]

    return transSet


class Cluster:

    def __init__(self, ID):
        self.ID = ID
        self.trans_nodes = {}
        self.customers = {}
        self.neighbours = []
        self.reference = []
        self.demand = 0
        self.TW = [0, 0]
        self.Dis = {}
        self.HC_sequence = []
        self.HC_cost = []
        self.service_time = 0

    def cluster_dis_matrix(self, Full_dis):
        self.Dis = cluster_matrix(self, Full_dis)

    def Create_transSet(self, dis, clusters):
        self.trans_nodes = transSet(self, dis, clusters)

    def Is_node_here(self, ID):
        return ID in self.customers.keys()


class Hexo:
    trans_percentage = 0.3

    def __init__(self, orgin, r):
        self.ID = 0
        Co = 0.8660254037844386
        self.r = r
        self.d = r * Co
        self.org = orgin
        self.corners = {}
        self.corners["est"] = (self.org[0] + r, self.org[1])
        self.corners["wst"] = (self.org[0] - r, self.org[1])
        self.corners["dwn_e"] = (self.org[0] + r/2, self.org[1] - self.d)
        self.corners["dwn_w"] = (self.org[0] - r/2, self.org[1] - self.d )
        self.corners["up_e"] = (self.org[0] + r/2, self.org[1] + self.d)
        self.corners["up_w"] = (self.org[0] - r/2, self.org[1] + self.d)

        self.area = round(3*3**(0.5)*self.r**2 / 2, 4)

        self.trans_nodes = {}
        self.customers = {}
        self.neighbours = []
        self.Time_measure = 0
        self.reference = []
        self.demand = 0
        self.TW = [0, 0]

        self.Dis = {}
        self.T_dis = {}
        self.HC_sequence = []
        self.HC_cost = []
        self.service_time = 0

    def cluster_dis_matrix(self, Full_dis):
        self.Dis = cluster_matrix(self, Full_dis)

    def Create_transSet(self, dis, clusters):
        self.trans_nodes = transSet(self, dis, clusters)

    def Drawing(self):
        # Create a hexagonal object
        hex = RegularPolygon(self.org, numVertices=6, radius=self.r,
                             orientation=np.radians(30),
                             facecolor="green", alpha=0.2, edgecolor='k')
        return hex

    def Check_if_inside(self, point):
        inside = 0
        Dis = euclidean_dis
        Corners = []
        comulative_area = 0
        for key1, key2 in zip(["wst", "up_w", "up_e", "est", "dwn_e", "dwn_w"], ["up_w","up_e","est","dwn_e","dwn_w","wst"]):
            Corners.append(self.corners[key1])
            a = Dis(self.corners[key1], point)
            b = Dis(self.corners[key2], point)
            c = Dis(self.corners[key1], self.corners[key2])
            s = (a+b+c)/2
            comulative_area += sqrt(s*(s-a)*(s-b)*(s-c))
        if round(comulative_area, 4) <= self.area:
            inside = 1
        return inside

    def time_window_calc(self):
        self.TW[0] = min([cus.TW[0] for cus in self.customers.values()])
        self.TW[1] = min([cus.TW[1] for cus in self.customers.values()]) #- self.service_time

    def Is_node_here(self, ID):
        # Check if the customer is in the cluster or not
        return ID in self.customers.keys()

    def remove_customer(self, customer):

        del self.customers[customer.ID]
        del self.T_dis[customer.ID]
        for cus_ID in self.T_dis.keys():
            del self.T_dis[cus_ID][customer.ID]

        if len(self.customers) <= 1:
            self.T_dis = {}

        # self.Calculate_time_measure()

    def add_customer(self, customer, New_T_dis={}):
        if New_T_dis:
            for cus_ID in self.customers.keys():
                if cus_ID  in self.T_dis.keys():
                    self.T_dis[cus_ID][customer.ID] = New_T_dis[cus_ID]
                else:
                    self.T_dis[cus_ID] = {customer.ID: New_T_dis[cus_ID]}

            self.customers[customer.ID] = customer
            self.T_dis[customer.ID] = New_T_dis
            # self.Calculate_time_measure()
        else:
            self.customers[customer.ID] = customer
