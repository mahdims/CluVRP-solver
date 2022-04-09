import os
import sys
import time
import getopt
from os import listdir
from os.path import isfile, join
import pandas as pd
sys.path.append("/home/mahdi/Google Drive/PostDoc/Scale vehicle routing/Code - git/VRP-aggregation")

from utils import read, write
from utils import Distance
from clustering import Clustering
from Aggregation import aggregationScheme, aggregation
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
            clu.Create_transSet(Data["Full_dis"], Data["Clusters"], trans_percentage)

    # Create the aggregation scheme
    agg_scheme = aggregationScheme(ref="Centroid", cscost="LB", cstime="SHC", inter="Ref2Ref",
                                   disAgg="OneTsp", entry_exit="Nearest")
    # Aggregation
    Data, clu_dis = aggregation(Data, agg_scheme)
    # compute and write the aggregated distance/consumption file for VRP solver
    # path_2_dis_mat = Write_AggDis_mat(Data, path_2_instance, clu_dis)
    # write the aggregated input file for VRP solver
    # path_2_instance = Write_AggInstance(path_2_instance, Data)
    Plots.Draw_on_a_plane(Data, [], 0, 0)

    # Run the VRP solver
    # objVal, Master_route = VRP_Model_SC(Data, clu_dis)
    objVal, Master_route = LNS_Algorithm.LNS(Data, clu_dis)
    #objVal, Master_route = Naive_LNS_Algorithm.LNS(Data, clu_dis)

    # Dis-aggregation
    Real_tours = []
    Total_Cost = 0
    for route in Master_route:
        Tour, Cost = agg_scheme.dis_aggregation(Data, route)
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
    #return


if __name__ == "__main__":
    # run_aggregation_disaggregation(sys.argv[1:])
    # file_names = glob.glob("data/Clu/Golden/*.gvrp")
    results = []
    number_runs = 1
    data_dir = "./GVRP"
    onlyfiles = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]
    # instance_name = "P-n22-k2-C11-V2.gvrp"
    for instance_name in onlyfiles:
    # for file in ["data/Clu/Golden/Golden_10-C30-N324.gvrp"]: # file_names:
        # M = int(file.split("k")[1].split(".vrp")[0])
        # real_name = file.split(".")[0].split("/")[-1].replace("C", "").replace("N", "").split("-") # Goldden
        # real_name = file.split("/")[-1].replace(".vrp", "").split("-")[:-1] # Li
        # Only run the ones that have 15 customers in a clusters . This is to test the K-nearest
        # if math.ceil(int(real_name[2]) / int(real_name[1])) != 15:
        #    continue
        for trans_percentage in [1]:
            BestObj = 1000000000
            Total_time = 0
            Total_obj = 0
            for run in range(number_runs):
                Vehicle, Obj, Run_time = run_aggregation_disaggregation(None, file)
                if Obj < BestObj:
                    BestObj = Obj

                Total_obj += Obj
                Total_time += Run_time

            results.append(real_name + [Vehicle, str(trans_percentage)] +
                           [str(BestObj), round(Total_obj/number_runs, 4), round(Total_time/number_runs, 4)])
            # write.pickle_dump(results, "./lowerbound/projection_knearest")

    df1 = pd.DataFrame(results, columns=["Name", "N", "M", "K", 'k-nearest', 'Best.Obj', "Avg.Obj", 'Avg.Time'])
    df1.to_csv("data/GVRP.csv")


