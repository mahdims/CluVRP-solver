import os
import sys
import time
import getopt
import glob
import pandas as pd
import pickle
import numpy as np
import itertools as it
sys.path.append("/home/mahdi/Google Drive/PostDoc/Scale vehicle routing/Code - git/VRP-aggregation")

from utils import read
from utils import Distance
from clustering import Clustering
from Aggregation import aggregationScheme, aggregation
from vrp_solver import VRP_Exact_Solver
from utils import write
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
        pass
        #print("No input file is given by command line. \n")

    # print("We are solving %s" % file_name)
    # print("The distance matrix is %s" % Dis_mat_name)

    path_2_instance = CWD + "/" + file_name
    # path_2_dis_mat = CWD.replace("projection", "data") + "/dis_matrix/" + Dis_mat_name
    return path_2_instance


def scheme_indep_error(Data, clu_dis):
    error = 0
    file_obj = open("./data/Clu/SHPs/%s" % Data["Instance_name"], 'rb')
    All_SHPs = pickle.load(file_obj)
    file_obj.close()

    for clu in Data["Clusters"].values():
        Hamiltonian_paths = All_SHPs[clu.ID]
        if len(Hamiltonian_paths) == 1:
            Diff_cost = 0
        else:
            Diff_cost = max(Hamiltonian_paths.values()) - min(Hamiltonian_paths.values())

        error += Diff_cost
    max_diff = 0
    for clu1, clu2 in it.combinations(Data["Clusters"].values(), 2):
        min_dis = max(Data["Full_dis"].values())
        max_dis = 0
        for i, j in zip(clu1.customers.keys(), clu2.customers.keys()):
            dis = Data["Full_dis"][(i, j)]
            if dis > max_dis:
                max_dis = dis
            if dis < min_dis:
                min_dis = dis

        diff = max_dis - min_dis
        if diff > max_diff:
            max_diff = diff

    error += (len(Data["Clusters"]) - 1) * max_diff

    max_depot_dis = 0
    for clu in Data["Clusters"].values():
        min_dis = max(Data["Full_dis"].values())
        max_dis = 0
        for i in clu.customers.keys():
            diff_in = Data["Full_dis"][('D0', i)]
            diff_out = Data["Full_dis"][(i, 'D1')]
            if diff_in > max_dis:
                max_dis = diff_in
            if diff_in < min_dis:
                min_dis = diff_in

        diff = max_dis - min_dis
        if diff > max_depot_dis:
            max_depot_dis = diff

    error += Data["Vehicles"] * max_depot_dis

    return error


def error_type2(Data, clu_dis):
    error = 0
    file_obj = open("./data/Clu/SHPs/%s" % Data["Instance_name"], 'rb')
    All_SHPs = pickle.load(file_obj)
    file_obj.close()

    for clu in Data["Clusters"].values():
        Hamiltonian_paths = All_SHPs[clu.ID]
        if len(Hamiltonian_paths) == 1:
            MaxHP_cost = list(Hamiltonian_paths.values())[0]
        else:
            MaxHp, MaxHP_cost = max(Hamiltonian_paths.items(), key=lambda x: x[1])

        error += MaxHP_cost - clu.service_time

    # For now we ignore the second and third part of this error
    # since the dis-aggregation use nearest and aggregation is also use nearest to estimate the distance

    return error


def error_type1(Data, clu_dis):
    error = 0
    file_obj = open("./data/Clu/SHPs/%s" % Data["Instance_name"], 'rb')
    All_SHPs = pickle.load(file_obj)
    file_obj.close()

    for clu in Data["Clusters"].values():
        Hamiltonian_paths = All_SHPs[clu.ID]
        if len(Hamiltonian_paths) == 1:
            MaxHP_cost = list(Hamiltonian_paths.values())[0]
            MinHP_cost = MaxHP_cost
        else:
            MaxHp, MaxHP_cost = max(Hamiltonian_paths.items(), key=lambda x: x[1])
            MinHP, MinHP_cost = min(Hamiltonian_paths.items(), key=lambda x: x[1])

        error += max(MaxHP_cost - clu.service_time, clu.service_time - MinHP_cost)

    max_inter_dist = 0
    for clu1, clu2 in it.combinations(Data["Clusters"].values(), 2):
        for i, j in zip(clu1.customers.keys(), clu2.customers.keys()):
            diff = abs(Data["Full_dis"][(i, j)] - clu_dis[clu1.ID, clu2.ID])
            if diff > max_inter_dist:
                max_inter_dist = diff

    error += (len(Data["Clusters"]) - 1) * max_inter_dist

    max_dis_to_depot = 0
    max_dis_from_depot = 0
    for clu in Data["Clusters"].values():
        for i in clu.customers.keys():
            diff_in = abs(Data["Full_dis"][('D0', i)] - clu_dis["D0", clu.ID])
            diff_out = abs(Data["Full_dis"][(i, 'D1')] - clu_dis[clu.ID, 'D0'])
            if diff_in > max_dis_to_depot:
                max_dis_to_depot = diff_in

            if diff_out > max_dis_from_depot:
                max_dis_from_depot = diff_out

    error += min(len(Data["Clusters"]), Data["Vehicles"]) * (max_dis_to_depot + max_dis_from_depot)
    return error


def run_error_bounds(arg, filename):
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
            clu.Create_transSet(Data["Full_dis"], Data["Clusters"], trans_percentage)
    
    # Create the aggregation scheme
    agg_scheme = aggregationScheme(ref="Centroid", cscost="SHC", cstime="SHC", inter="Ref2Ref",
                                   disAgg="Sequential", entry_exit="Nearest")
    # Aggregation
    Data, clu_dis = aggregation(Data, agg_scheme)
    # compute and write the aggregated distance/consumption file for VRP solver
    # path_2_dis_mat = Write_AggDis_mat(Data, path_2_instance, clu_dis)
    # write the aggregated input file for VRP solver
    # path_2_instance = Write_AggInstance(path_2_instance, Data)

    error1 = error_type1(Data, clu_dis)
    # error2 = error_type2(Data, clu_dis)
    error_new = scheme_indep_error(Data, clu_dis)
    # print(f"Total error = {error1+error2}")
    # print(obj_calc(Data["Full_dis"], Master_route))
    # Total_Cost = obj_calc(Data["Full_dis"], Master_route)
    # print(f"Number of vehicles = {len(Master_route)}")
    # Draw the final tours all together
    # Plots.Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time)
    # save the CUSTOMERS SEQUENCE
    # save_the_customers_sequence(CWD,file_name, Real_tours,Total_Cost,Run_time )

    Mean_dis = closeness(Data)

    return 2 * error1, error_new, Mean_dis


def closeness(Data):
    Avg_dist = []
    for i in Data["Customers"].keys():
        temp = []
        for j in Data["Customers"].keys():
            if i != j:
                temp.append(Data["Full_dis"][i, j])

        Avg_dist.append(np.mean(sorted(temp)[:5]))

    return np.mean(Avg_dist)


if __name__ == "__main__":
    # run_aggregation_disaggregation(sys.argv[1:])
    file_names = glob.glob("data/Clu/Golden/*.gvrp")
    results = []

    for file in file_names:
        real_name = file.split(".")[0].split("/")[-1].replace("C", "").replace("N", "").split("-")

        trans_percentage = 1 # 0.7 0.5 0.3 0.1

        error_old, error_new, Mean_dis = run_error_bounds(None, file)
        #print(error1)
        results.append(real_name + [error_old, error_new, Mean_dis])

        write.pickle_dump(results, "./lowerbound/errors")

    import pickle
    with open("./lowerbound/errors", "rb") as ffile:
        results = pickle.load(ffile)
    df1 = pd.DataFrame(results,
                       columns=["Name", "N", "M", 'Scheme_dep_Error', 'Scheme_indep_Error', 'Mean_dis'])
    df1.to_csv("./lowerbound/closeness.csv")

