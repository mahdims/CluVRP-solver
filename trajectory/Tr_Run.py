import sys
sys.path.append("/home/mahdi/Google Drive/PostDoc/Scale vehicle routing/Code - git/VRP-aggregation")

import os
import sys
import time
import getopt
import math
import itertools as it
from utils import read
from utils import Distance
from clustering import Clustering
import Agg_Disagg
from vrp_solver import LNS_Algorithm, Naive_LNS_Algorithm
from utils import Plots


def obj_calc(dist, routes):
    cost = 0
    for route in routes:
        pre_cus = route[1][0]
        for cus in route[1][1:]:
            cost += dist[pre_cus, cus]
            pre_cus = cus

    return cost

def get_files_name(arg, file_name):
    # This function will get the arg and return the path to instance files and distance matrix if specified
    # file_name = "Clu/Golden/Golden_16-C33-N481.gvrp"
    # file_name = "Clu/Li/560.vrp-C113-R5.gvrp"
    # file_name = "Arnold/Leuven1.txt"
    # Dis_mat_name = "vrp_solver_matrix.txt"
    TW_indicator = 0
    CWD = os.getcwd()

    try:
        opts, args = getopt.getopt(arg, "i:m", ["Input=", "DistanceMatrix="])
        for opt, arg in opts:
            if opt in ("-i", "--Input"):
                file_name = arg
            elif opt in ("-m", "--DistanceMatrix"):
                Dis_mat_name = arg

    except getopt.GetoptError:
        sys.exit('Run_with_Aggregation.py -i <Input> -n <DistanceMatrix>')

    if not len(opts):
        print("No input file is given by command line. \n")

    print("We are solving %s" % file_name)
    # print("The distance matrix is %s" % Dis_mat_name)

    path_2_instance = CWD + "/" + file_name
    # path_2_dis_mat = CWD.replace("projection", "data") + "/dis_matrix/" + Dis_mat_name
    return path_2_instance


def run_aggregation_disaggregation(arg, filename):

    path_2_instance = get_files_name(arg, filename)
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

    # Aggregation
    Data, clu_dis = Agg_Disagg.aggregation(Data)

    # Run the VRP solver
    # objVal, Master_route = VRP_Model_SC(Data, clu_dis)
    objVal, Master_route = LNS_Algorithm.LNS(Data, clu_dis)
    #objVal, Master_route = Naive_LNS_Algorithm.LNS(Data, clu_dis)

    # Dis-aggregation
    Real_tours = []
    Total_Cost = 0
    for route in Master_route:
        Tour, Cost = Agg_Disagg.dis_aggregation(Data, route)
        Real_tours.append([Cost, Tour])
        Total_Cost += Cost

    Run_time = time.time() - Timer_start
    print(f"Total cost = {Total_Cost}")
    print(obj_calc(Data["Full_dis"], Real_tours))
    Total_Cost = obj_calc(Data["Full_dis"], Real_tours)
    print(f"Runtime = {Run_time}")
    print(f"Number of vehicles = {len(Master_route)}")
    # Draw the final tours all together
    # Plots.Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time)
    # save the CUSTOMERS SEQUENCE
    # save_the_customers_sequence(CWD,file_name, Real_tours,Total_Cost,Run_time )
    return len(Master_route), Total_Cost, Run_time


import glob
import pandas as pd

if __name__ == "__main__":
    file_names = glob.glob("data/Clu/Golden/*.gvrp")
    results = []
    number_runs = 1
    for file in file_names[2:3]:
        # M = int(file.split("k")[1].split(".vrp")[0])
        real_name = file.split(".")[0].split("/")[-1].replace("C", "").replace("N", "").split("-")

        BestObj = 1000000000
        Total_time = 0
        Total_obj = 0

        for run in range(number_runs):
            Vehicle, Obj, Run_time = run_aggregation_disaggregation(None, file)
            if Obj < BestObj:
                BestObj = Obj

            Total_obj += Obj
            Total_time += Run_time

        results.append(real_name + [Vehicle, BestObj, round(Total_obj/number_runs, 4),round(Total_time/number_runs, 4)])

    df1 = pd.DataFrame(results,
                       columns=["Name", "N", "M", "K", 'Best.Obj', "Avg.Obj",'Avg.Time'])
    df1.to_csv("Results_Li_AS1.csv")
