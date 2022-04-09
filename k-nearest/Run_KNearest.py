import os
import sys
import time
import getopt
import glob
import pandas as pd

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
        print("No input file is given by command line. \n")

    print("We are solving %s" % file_name)
    # print("The distance matrix is %s" % Dis_mat_name)

    path_2_instance = CWD + "/" + file_name
    # path_2_dis_mat = CWD.replace("projection", "data") + "/dis_matrix/" + Dis_mat_name
    return path_2_instance



def run_aggregation_LB(arg, filename):

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
    agg_scheme = aggregationScheme(ref="Centroid", cscost="LB", cstime="LB", inter="Nearest",
                                   disAgg="OneTsp", entry_exit="Nearest")
    # Aggregation
    Data, clu_dis = aggregation(Data, agg_scheme)
    # compute and write the aggregated distance/consumption file for VRP solver
    # path_2_dis_mat = Write_AggDis_mat(Data, path_2_instance, clu_dis)
    # write the aggregated input file for VRP solver
    # path_2_instance = Write_AggInstance(path_2_instance, Data)

    # Run the VRP solver
    objVal, Master_route = VRP_Exact_Solver.VRP_Model_SC(Data, clu_dis)
    # objVal, Master_route = LNS_Algorithm.LNS(Data, clu_dis)
    # objVal, Master_route = Naive_LNS_Algorithm.LNS(Data, clu_dis)

    Run_time = time.time() - Timer_start
    print(f"Total cost = {objVal}")
    # print(obj_calc(Data["Full_dis"], Master_route))
    # Total_Cost = obj_calc(Data["Full_dis"], Master_route)
    print(f"Runtime = {Run_time}")
    # print(f"Number of vehicles = {len(Master_route)}")
    # Draw the final tours all together
    # Plots.Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time)
    # save the CUSTOMERS SEQUENCE
    # save_the_customers_sequence(CWD,file_name, Real_tours,Total_Cost,Run_time )
    return len(Master_route), objVal, Run_time


if __name__ == "__main__":
    # run_aggregation_disaggregation(sys.argv[1:])
    file_names = glob.glob("data/Clu/Golden/*.gvrp")
    results = []
    number_runs = 1
    '''
    file_names = \
        '\t\tGolden_1	C	17	N	241	\n	'\
    '	Golden_1	C	17	N	241	\n	'\
    '	Golden_11	C	34	N	400	\n	'\
    '	Golden_1	C	49	N	241	\n	'\
    '	Golden_11	C	40	N	400	\n	'\
    '	Golden_11	C	37	N	400	\n	'\
    '	Golden_6	C	57	N	281	\n	'\
    '	Golden_15	C	45	N	397	\n	'\
    '	Golden_10	C	36	N	324	\n	'\
    '	Golden_11	C	31	N	400	\n	'\
    '	Golden_19	C	52	N	361	\n	'\
    '	Golden_20	C	43	N	421	\n	'\
    '	Golden_11	C	50	N	400	\n	'\
    '	Golden_12	C	35	N	484	\n	'\
    '	Golden_10	C	41	N	324	\n	'\
    '	Golden_15	C	50	N	397	\n	'\
    '	Golden_3	C	58	N	401	\n	'\
    '	Golden_15	C	57	N	397	\n	'\
    '	Golden_10	C	54	N	324	\n	'\
    '	Golden_20	C	47	N	421	\n	'\
    '	Golden_2	C	65	N	321	\n	'\
    '	Golden_10	C	65	N	324	\n	'\
    '	Golden_12	C	41	N	484	\n	'\
    '	Golden_8	C	49	N	441	\n	'\
    '	Golden_10	C	47	N	324	\n	'\
    '	Golden_8	C	56	N	441	\n	'\
    '	Golden_8	C	45	N	441	\n	'\
    '	Golden_12	C	44	N	484	\n	'\
    '	Golden_16	C	44	N	481	\n	'\
    '	Golden_11	C	67	N	400	\n	'\
    '	Golden_3	C	51	N	401	\n	'\
    '	Golden_12	C	61	N	484	\n	'\
    '	Golden_16	C	61	N	481	\n	'\
    '	Golden_20	C	71	N	421	\n	'\
    '	Golden_15	C	67	N	397	\n	'\
    '	Golden_11	C	58	N	400	\n	'\
    '	Golden_11	C	45	N	400	\n	'\
    '	Golden_4	C	61	N	481	\n	'\
    '	Golden_11	C	80	N	400	\n	'\
    '	Golden_19	C	73	N	361	\n	'\
    '	Golden_3	C	81	N	401	\n	'\
    '	Golden_20	C	61	N	421	\n	'\
    '	Golden_20	C	85	N	421	\n	'\
    '	Golden_12	C	38	N	484	\n	'\
    '	Golden_15	C	80	N	397	\n	'\
    '	Golden_4	C	81	N	481	\n	'\
    '	Golden_8	C	89	N	441	\n	'\
    '	Golden_12	C	54	N	484	\n	'\
    '	Golden_12	C	81	N	484	\n	'\
    '	Golden_8	C	74	N	441	\n	'\
    '	Golden_12	C	49	N	484	\n	'\
    '	Golden_12	C	97	N	484	\n	'\
    '	Golden_4	C	97	N	481	\n	'\
    '	Golden_12	C	70	N	484	\n	'\
    '	Golden_16	C	69	N	481	\n	'\
    '	Golden_16	C	97	N	481	\n	'\
    '	Golden_16	C	81	N	481	\n	'\
    '	Golden_8	C	63	N	441	\n	'\
    '	Golden_2	C	33	N	321	\n	'
    file_names = file_names.split("\n")
    file_names = ["data/Clu/Golden/" +line.replace("\t","",2).replace("\t","-",1).replace("\t","",1).replace("\t","-",1).replace("\t","")
                  + ".gvrp" for line in file_names]
    '''
    for file in file_names: #["data/Clu/Li/640.vrp-C129-R5.gvrp"]: #
        real_name = file.split(".")[0].split("/")[-1].replace("C", "").replace("N", "").split("-")

        BestObj = 1000000000
        Total_time = 0
        Total_obj = 0
        trans_percentage = 1 # 0.7 0.5 0.3 0.1

        for run in range(number_runs):
            Vehicle, Obj, Run_time = run_aggregation_LB(None, file)
            if Obj < BestObj:
                BestObj = Obj

            Total_obj += Obj
            Total_time += Run_time

        results.append(real_name + [Vehicle, Obj, Run_time]) # round(Total_obj/number_runs, 4),round(Total_time/number_runs, 4)])

        write.pickle_dump(results, "./lowerbound/LBs")

    # import pickle
    #with open("./lowerbound/LBs", "rb") as ffile:
    #    results = pickle.load(ffile)
    df1 = pd.DataFrame(results,
                       columns=["Name", "N", "M", "K", 'LowerBound', 'Time'])
    df1.to_csv("./lowerbound/Results_LB.csv")

