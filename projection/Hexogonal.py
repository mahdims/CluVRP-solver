import copy
import math
import time
import statistics as st
import itertools as it
import numpy as np
from matplotlib.patches import RegularPolygon, Rectangle
from Honeycomb_Clustering import Calculate_time_distance
from TSP_Solver import TSP_model
from TSPTW_Solver import TSPTW_model



def euclidean_dis(A,B):

    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)

class Hexo:

    def __init__(self,orgin, r):
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

        self.area = round(3*3**(0.5)*self.r**2 / 2 , 4)

        self.Enter_exit_points = {}
        self.Calculate_entering_exiting()

        self.customers = {}
        self.neighbours = []
        self.Time_measure = 0
        self.centroid = []
        self.demand = 0
        self.TW = [0, 0]

        self.Dis = {}
        self.T_dis = {}
        self.HC_sequence = []
        self.HC_cost = []
        self.service_time = 0

    def Calculate_entering_exiting(self):
        for key1, key2 in zip(["up_w", "up_e", "est", "dwn_e", "dwn_w" ,"wst"],
                              ["up_e", "est", "dwn_e", "dwn_w", "wst" ,"up_w"]):
            if "_" in key1 and "_" in key2:
                new_key = key1.split("_")[0]
            elif "_" in key1:
                new_key = key1
            else:
                new_key = key2

            a = self.corners[key1]
            b = self.corners[key2]
            self.Enter_exit_points[new_key] = ((a[0]+b[0])/2, (a[1]+b[1])/2)

    def cluster_dis_matrix(self, Data):
        Dis = {}
        Full_dis = Data["Full_dis"]
        for a, b in it.combinations(self.customers.keys(), 2):
            if Full_dis:  # if the distance matrix is given by the file use that one
                Dis[(a, b)] = Full_dis[(a, b)]
                Dis[(b, a)] = Dis[(a, b)]
            else:  # if there is not distance matrix use the direct distances
                Dis[(a, b)] = euclidean_dis(self.customers[a].coord, self.customers[b].coord)
                Dis[(b, a)] = Dis[(a, b)]
        # Store the distance matrix for all nodes in one cluster
        self.Dis = Dis

    def Calculate_time_measure(self):
        print("we are calculating the time measure")
        if self.T_dis:
            self.Time_measure = st.mean([st.mean(self.T_dis[cus.ID].values()) for cus in self.customers.values()])
        else:
            self.Time_measure = 0

    def initial_T_dis_matrix(self, Data):
        print("Distance matrix!!")
        T_dis = {}
        for cus1, cus2 in it.combinations(self.customers.values(), 2):
            new_dis = Calculate_time_distance(Data, cus1, cus2)
            if cus1.ID not in T_dis.keys():
                T_dis[cus1.ID] = {cus2.ID: new_dis}
            else:
                T_dis[cus1.ID][cus2.ID] = new_dis

            if cus2.ID not in T_dis.keys():
                T_dis[cus2.ID] = {cus1.ID: new_dis}
            else:
                T_dis[cus2.ID][cus1.ID] = new_dis

        self.T_dis = T_dis

        self.Calculate_time_measure()

    def Centroid(self):
        if len(self.customers) == 1:
            self.centroid = list(self.customers.values())[0].coord
        else:
            self.centroid = sum([np.array(self.customers[a].coord) for a in self.customers.keys()]) / len(self.customers)
        return self.centroid

    def Hamiltonian_cycle(self, Data, TW_indicator):
        # note the hamiltonian cycle starts from the depot and end at the depot therefore we needs to add distances
        # Add the depot D0 and D1 to the distance matrix
        Dis = copy.copy(self.Dis)
        Full_dis = Data["Full_dis"]
        for a in self.customers.keys():
            if Full_dis:
                Dis[("D0", a)] = Full_dis[("D0", a)]
                Dis[(a, "D1")] = Dis[("D0", a)]
            else:
                Dis[("D0", a)] = euclidean_dis(self.customers[a].coord, Data["Customers"]["D0"].coord)
                Dis[(a, "D1")] = Dis[("D0", a)]

        # calculate the hamiltonian cycle of the customers
        TSP_Nodes = copy.copy(self.customers)
        TSP_Nodes["D0"] = Data["depot"]
        TSP_Nodes["D1"] = Data["depot"]
        time_start = time.time()
        if TW_indicator:
            self.HC_sequence, self.HC_cost = TSPTW_model(Dis, Nodes=TSP_Nodes, start_time=0)
        else:
            self.HC_sequence, self.HC_cost = TSP_model(Dis, Nodes=TSP_Nodes)

        if not self.HC_sequence:
            print("Cluster %s is infeasible" % self.ID)
            return 0
        else:
            print("We find the Hamiltonian cycle for cluster %s in %s sec" % (self.ID, round(time.time()-time_start,3)))
            self.HC_sequence.remove("D0")
            self.HC_sequence.remove("D1")
            self.HC_cost = self.HC_cost - Dis[("D0", self.HC_sequence[0])] - Dis[(self.HC_sequence[-1], "D1")]
            return 1

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
        for key1, key2 in zip(["wst","up_w","up_e","est","dwn_e","dwn_w"] , ["up_w","up_e","est","dwn_e","dwn_w","wst"]):
            Corners.append(self.corners[key1])
            a = Dis(self.corners[key1], point)
            b = Dis(self.corners[key2], point)
            c = Dis(self.corners[key1], self.corners[key2])
            s = (a+b+c)/2
            comulative_area += math.sqrt(s*(s-a)*(s-b)*(s-c))
        if round(comulative_area, 4) <= self.area:
            inside = 1
        return inside

    def time_window_calc(self):
        self.TW[0] = min([cus.TW[0] for cus in self.customers.values()])
        self.TW[1] = min([cus.TW[1] for cus in self.customers.values()]) #- self.service_time

    def Is_node_here(self, ID):
    #Check if the customer is in the cluster or not
        return ID in self.customers.keys()

    def remove_customer(self, customer):

        del self.customers[customer.ID]
        del self.T_dis[customer.ID]
        for cus_ID in self.T_dis.keys():
            del self.T_dis[cus_ID][customer.ID]

        if len(self.customers) <= 1:
            self.T_dis = {}

        self.Calculate_time_measure()

    def add_customer(self, customer, New_T_dis={}):
        if New_T_dis:
            for cus_ID in self.customers.keys():
                if cus_ID  in self.T_dis.keys():
                    self.T_dis[cus_ID][customer.ID] = New_T_dis[cus_ID]
                else:
                    self.T_dis[cus_ID] = {customer.ID: New_T_dis[cus_ID]}

            self.customers[customer.ID] = customer
            self.T_dis[customer.ID] = New_T_dis
            self.Calculate_time_measure()
        else:
            self.customers[customer.ID] = customer
