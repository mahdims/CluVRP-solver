import numpy as np
import pandas as pd
import copy
from matplotlib.patches import RegularPolygon, Rectangle
from sklearn.cluster import KMeans
import math
import networkx as nx
import itertools as it
from TSP_Solver import TSP_model

def euclidean_dis(A,B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


class Customer:
    def __init__(self, ID, coord, d, TW, ST):
        self.ID = ID
        self.coord = coord
        self.demand = d
        self.TW = TW
        self.service_time = ST

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
        self.centroid = []
        self.demand = 0
        self.TW = [0,0]

        self.Dis = {}
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

    def Centroid(self):
        if len(self.customers) == 1:
            self.centroid = list(self.customers.values())[0].coord
        else:
            self.centroid = sum([np.array(self.customers[a].coord) *
                                  self.customers[a].demand for a in self.customers.keys()]) / self.demand
        return self.centroid

    def Hamiltonian_cycle(self,Data):

        # create the distance matrix
        # note the hamiltonian cycle starts from the depot and end at the depot therefore we needs to add distances
        # from the depot
        Dis = {}
        Full_dis = Data["Full_dis"]
        for a,b in it.combinations(self.customers.keys(), 2):
            if Full_dis: # if the distance matrix is given by the file use that one
                Dis[(a,b)] = Full_dis[(a,b)]
                Dis[(b, a)] = Dis[(a, b)]
            else: # if there is not distance matrix use the direct distances
                Dis[(a,b)] = euclidean_dis(self.customers[a].coord, self.customers[b].coord)
                Dis[(b,a)] = Dis[(a,b)]

        # Add the depot 0 and 1 to the distance matrix
        for a in self.customers.keys():
            if Full_dis:
                Dis[("D0",a)] = Full_dis[("D0",a)]
                Dis[(a,"D1")] = Dis[("D0",a)]
            else:
                Dis[("D0", a)] = euclidean_dis(self.customers[a].coord, Data["Customers"]["D0"].coord)
                Dis[(a, "D1")] = Dis[("D0", a)]

        # Store the distance matrix for all nodes in one cluster
        self.Dis = Dis
        # calculate the hamiltonian cycle of the customers
        TSP_Nodes = copy.copy(self.customers)
        TSP_Nodes["D0"] = Data["depot"]
        TSP_Nodes["D1"] = Data["depot"]
        self.HC_sequence, self.HC_cost = TSP_model(Dis, Nodes=TSP_Nodes, start_time=0)
        self.HC_sequence.remove("D0")
        self.HC_sequence.remove("D1")
        self.HC_cost = self.HC_cost - Dis[("D0", self.HC_sequence[0])] - Dis[(self.HC_sequence[-1], "D1")]

    def Drawing(self):
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
        self.TW[0] = min([cus.TW[0] for cus in self.customers.values()] )
        self.TW[1] = min([cus.TW[1] for cus in self.customers.values()]) #- self.service_time

    def add_customer(self, customer):
        self.customers[customer.ID] = customer

    def Is_node_here(self, ID):
    #Check if the customer is in the cluster or not
        return ID in self.customers.keys()


def read_the_data(folder, file_name, Dis_mat_name = None):
    np.random.seed(0)
    Path_2_file = '/home/mahdi/Documents/zukunft.de/input_files/%s/%s.txt' %(folder, file_name)
    f = open(Path_2_file, "r")
    lines = list(f)
    Q = int(lines[-3].split("/")[1])
    C = int(lines[-2].split("/")[1])
    R = int(lines[-1].split("/")[1])
    f.close()
    data = pd.read_csv(Path_2_file, sep="\t", skipfooter=4,engine='python')
    data.columns = ["Type",	"x",	"y",	"Demand",	"Ready",	"Due",	"Service" ,"Waste"]
    clean_data = {}
    stations_coord = {}
    customers_coord = {}
    customers = {}
    counter = 1
    for inx , s in enumerate(data["Type"]):
        if "d" in s:
            depot = Customer("D0", (data["x"][inx], data["y"][inx]), data["Demand"][inx],
                                         (data["Ready"][inx], data["Due"][inx]), data["Service"][inx])
        elif "f" in s:
            stations_coord[inx] = (data["x"][inx], data["y"][inx])
        else:
            customers_coord[inx] = (data["x"][inx],data["y"][inx])
            cus_ID = data.index[inx]
            customers[cus_ID] = Customer(cus_ID,(data["x"][inx],data["y"][inx]),data["Demand"][inx],
                     (data["Ready"][inx], data["Due"][inx]),data["Service"][inx])

    # read the distance matrix file
    file = open("%s.txt" % Dis_mat_name)
    lines = list(file)
    file.close()
    Full_dis = {}
    Full_consump = {}
    for line_inx in range(0, len(lines), 6):
        arc = tuple(lines[line_inx + 1].replace("\n", "").split(" "))
        Full_dis[arc] = int(lines[line_inx + 3].replace("\n", "").split("\t")[3]) / 1000
        Full_consump[arc] = int(lines[line_inx + 5].replace("\n", "").split("\t")[3]) / 1000

    customers_No = len(customers_coord)
    clean_data["Full_dis"] = Full_dis
    clean_data["Full_consump"] = Full_consump
    clean_data["depot"] = depot
    clean_data["S_coord"] = stations_coord
    clean_data["C_coord"] = customers_coord
    clean_data["Customers"] = customers
    clean_data["N_C"] = customers_No
    clean_data["Demand"] = data["Demand"]
    clean_data["Clusters"] = {}
    clean_data["Q"] = Q
    clean_data["C"] = C
    clean_data["R"] = R
    clean_data["Axu_depot"] = max(customers_coord.keys()) + 1

    # erase this after test
    clean_data["depot"].TW= (0,23000)
    return clean_data


def K_means_Clustering(clean_data):
    customers_x = clean_data["Cx"]
    customers_y = clean_data["Cy"]
    # create kmeans object
    N_of_clusters = 10
    kmeans = KMeans(n_clusters=N_of_clusters)
    # fit kmeans object to data
    kmeans.fit(zip(customers_x.values(),customers_y.values()))
    # save new clusters for chart
    y_km = kmeans.fit_predict(zip(customers_x.values(),customers_y.values()))

    for cl in range(N_of_clusters):
        Clu = 0
        #Clu = Cluster(np.array(customers_x.values())[y_km == cl], np.array(customers_y.values())[y_km==cl], list(clean_data["Demand"][-customers_No:][y_km==cl]))
        Clu.K_mean_center =  kmeans.cluster_centers_[cl]
        clean_data["Clusters"].append(Clu)

    return clean_data


def Honeycomb_Clustering(clean_data):
    Co = 0.8660254037844386
    r = 10
    d = r * Co
    vcoord = []
    hcoord = []
    # Create the clusters network
    for inx, x in enumerate(np.arange(0, 120, 1.5 * r)):
        inx += 1
        indic = inx - int(inx / 2) * 2 == 0
        for y in np.arange(indic * d, 120, 2 * d):
            vcoord.append(y)
            hcoord.append(x)
    # Actually creating the clusters
    count = 1
    for x, y in zip(hcoord, vcoord):
        new_hex = Hexo((x, y), r)
        clean_data["Clusters"][count] = new_hex
        count += 1
    # Find which customer is inside which cluster
    for cus in clean_data["Customers"].values():
        for Clu in clean_data["Clusters"].values():
            if Clu.Check_if_inside(cus.coord):
                Clu.add_customer(cus)
                break

    ID_cont = 1
    used_clusters = []
    for key,clu in clean_data["Clusters"].items():
        # Only keep the clusters that have customers inside
        if clu.customers:
            # Assign the clusters ID
            clu.ID = "Cu" + str(ID_cont)
            ID_cont += 1
            # Calculate the total demand of a cluster
            clu.demand = sum([cus.demand for cus in clu.customers.values()])
            # Calculate the clusters centroid
            clu.Centroid()
            # Calculate the Shortest hamiltonian cycle with solving a TSP
            clu.Hamiltonian_cycle(clean_data)
            # compute the time service
            clu.service_time = int(clu.HC_cost )
            # Calculate the cluster time windows
            clu.time_window_calc()
            # store it as a used cluster
            used_clusters.append((clu.ID, clu))

    used_clusters = dict(used_clusters)
    clean_data["Clusters"] = used_clusters

    return clean_data
