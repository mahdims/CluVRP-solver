import sys
import os
import time
import itertools as it
sys.path.append("/home/mahdi/Google Drive/PostDoc/Scale vehicle routing/Code - git/VRP-aggregation")
from clustering import Clustering
from utils import read
from utils import Distance
from tsp_solver import TSP_Solver
import pickle
import glob


def initialization(file_name):
    path_2_instance = os.getcwd() +"/"+ file_name
    Timer_start = time.time()
    # read the data from  the text file
    Data = read.read_the_data(path_2_instance)
    # Create the full distance matrix
    Data["Full_dis"] = Distance.build_distance_matrix(Data["depot"], Data["Customers"])
    if not Data["Clusters"]:
        # Implement the honeycomb clustering
        Data = Clustering.Honeycomb_Clustering(Data)
    else:
        for clu in Data["Clusters"].values():
            clu.cluster_dis_matrix(Data["Full_dis"])
            clu.Create_transSet(Data["Full_dis"], Data["Clusters"])

    return Data


def calc_all_SHP(clu):
    Hamiltonian_paths = {}

    if len(clu.customers) == 1:
        nodes = tuple(list(clu.customers.keys()))
        Hamiltonian_paths[nodes] = list(clu.customers.values())[0].service_time
    elif len(clu.customers) == 2:
        nodes = tuple(list(clu.customers.keys()))
        Hamiltonian_paths[nodes] = clu.Dis[nodes] + sum([cus.service_time for cus in clu.customers.values()])
    else:
        for cus1, cus2 in it.combinations(clu.customers.keys(), 2):
            _, HP_cost = TSP_Solver.solve(clu.Dis, Nodes=clu.customers, start=cus1, end=cus2)
            Hamiltonian_paths[(cus1, cus2)] = HP_cost + sum([cus.service_time for cus in clu.customers.values()])

    return Hamiltonian_paths


def file_SHPs(Data, filename):

    all_SHPs = {}

    for clu in Data["Clusters"].values():
        all_SHPs[clu.ID] = calc_all_SHP(clu)

    file = open(f"./data/Clu/SHPs/{filename}", 'wb')
    # dump information to that file
    pickle.dump(all_SHPs, file)
    # close the file
    file.close()
    print(f"I dumped the Hamiltonian paths for {filename}")



if __name__ == "__main__":

    file_names = glob.glob("data/Clu/Golden/*.gvrp")
    for file in file_names:
        real_name = file.split(".")[0].split("/")[-1]
        Data = initialization(file)
        file_SHPs(Data, real_name)
