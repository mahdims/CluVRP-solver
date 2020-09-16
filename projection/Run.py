import subprocess as sub
import os
import sys
import time
import getopt
import math
import itertools as it
from read import read_the_data
from Clustering import Honeycomb_Clustering
from Aggregation import aggregationScheme, aggregation
from Write_files import Write_AggInstance, Write_AggDis_mat
from VRP_Exact_Solver import VRP_Model_SC, VRP_Model_2CF
from Plots import Draw_on_a_plane


def get_files_name(arg):
    # This function will get the arg and return the path to instance files and distance matrix if specified
    file_name = "Uchoa/X-n895-k37.vrp"
    Dis_mat_name = "vrp_solver_matrix.txt"
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

    path_2_instance = CWD.replace("projection", "data") + "/" + file_name
    # path_2_dis_mat = CWD.replace("projection", "data") + "/dis_matrix/" + Dis_mat_name
    return path_2_instance


def euclidean_dis(A, B):
    return math.sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2)


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


def run_aggregation_disaggregation(arg):
    CWD = os.getcwd()
    path_2_instance = get_files_name(arg)
    Timer_start = time.time()
    # read the data from  the text file
    Data = read_the_data(path_2_instance)
    # Create the full distance matrix
    Data["Full_dis"] = build_distance_matrix(Data["depot"], Data["Customers"])
    # Implement the honeycomb clustering
    Data = Honeycomb_Clustering(Data)
    # Create the aggregation scheme
    agg_scheme = aggregationScheme(ref="Centroid", cscost="SHC", cstime="SHC", inter="Nearest",
                                   disAgg="OneTsp", entry_exit="SHPs")
    # Aggregation
    Data, clu_dis = aggregation(Data, agg_scheme)
    # compute and write the aggregated distance/consumption file for VRP solver
    path_2_dis_mat = Write_AggDis_mat(Data, path_2_instance, clu_dis)
    # write the aggregated input file for VRP solver
    path_2_instance = Write_AggInstance(path_2_instance, Data)

    # Run the VRP solver
    objVal, Master_route = VRP_Model_SC(Data, clu_dis)
    # objVal, Master_route = VRP_Model_2CF(Data, clu_dis)

    # Dis-aggregation
    Real_tours = []
    Total_Cost = 0
    for route in Master_route:
        Tour, Cost = agg_scheme.dis_aggregation(Data, route)
        print(Cost, Tour)
        Real_tours.append([Cost, Tour])
        Total_Cost += Cost

    Run_time = time.time() - Timer_start
    print(f"Total cost = {Total_Cost}")
    print(f"Runtime = {Run_time}")
    # Draw the final tours all together
    Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time)
    # save the CUSTOMERS SEQUENCE
    # save_the_customers_sequence(CWD,file_name, Real_tours,Total_Cost,Run_time )
    

if __name__ == "__main__":
    run_aggregation_disaggregation(sys.argv[1:])