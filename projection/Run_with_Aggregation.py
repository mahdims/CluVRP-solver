import subprocess as sub
import os
import sys
import time
import getopt
import matplotlib.pyplot as plt
from read import read_the_data
from Honeycomb_Clustering import Honeycomb_Clustering
from Agg_Dis_Matrix import update_dis_mat
from Write_the_aggregated_file import Write_the_aggregated_file
from Dis_aggregation import Dis_aggregation
from Plots import plot_out

# current directory path
dir_path = os.path.dirname(os.path.realpath(__file__))

def Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time):
    fig, ax = plt.subplots(1)
    # aggregation solution
    ax.set_title("Aggregation Solution", fontsize=13.0)
    plot_out(ax, Data, Real_tours, Total_Cost, Run_time)
    plt.show()

def save_the_customers_sequence(CWD,file_name, Real_tours,Total_Cost,Run_time ):
    midoutput = open(CWD.replace("solver","route")+f"/output_data/customer_sequence/sequence_{file_name}" ,'w+')
    midoutput.write("Total Time in seconds: %s \n" %Run_time)
    for cost , l in Real_tours:
        str_rout = ""
        for n in l[:-1]:
            str_rout += str("%s->" %n)
        str_rout += "D0"
        midoutput.write(str(round(cost,3))+": "+ str_rout + "\n")
    midoutput.write("Total costs: %s" % round(Total_Cost,3))
    midoutput.close()


# Problem specification
def run_aggregation_disaggregation(arg):
    file_name = "kita_6.txt"
    Dis_mat_name = "vrp_solver_matrix.txt"
    TW_indicator = 0
    CWD = os.getcwd()

    try:
        opts, args = getopt.getopt(arg, "i:m:", ["Input=", "DistanceMatrix="])
        for opt, arg in opts:
            if opt in ("-i", "--Input"):
                file_name = arg
            elif opt in ("-m", "--DistanceMatrix"):
                Dis_mat_name = arg

    except getopt.GetoptError:
        sys.exit('Run_with_Aggregation.py -i <Input> -n <DistanceMatrix>')

    if not len(opts):
        print("No input file is given by command line. \n")
    if "e" in file_name:
        TW_indicator = 1

    print("We are solving %s" % file_name)
    print("The distance matrix is %s" % Dis_mat_name)

    path2file = CWD.replace("solver", "route") + "/input_data/instances/"
    path2matrix = CWD.replace("solver", "route") + "/output_data/"

    path_2_instance = path2file + file_name
    path_2_dis_mat = path2matrix + Dis_mat_name

    Timer_start = time.time()
    # read the data from  the text file
    Data = read_the_data(path_2_instance)
    # Implement the honeycomb clustering
    Data = Honeycomb_Clustering(Data)
    # compute and write the aggregated distance/consumption file for VRP solver
    path_2_dis_mat = update_dis_mat(Data, CWD, Dis_mat_name)
    # write the aggregated input file for VRP solver
    path_2_instance = Write_the_aggregated_file(Data, CWD, file_name)

    # Run the VRP solver
    path_2_VRP_solver = CWD.replace("solver", "vrp_solver")
    p = sub.Popen([f"{path_2_VRP_solver}/bin/TDRRRPOptimiser", path_2_instance, path_2_dis_mat], stdout=sub.PIPE, stderr=sub.PIPE,
                  universal_newlines=True)
    p.wait()
    # Get the output from the VRP solver
    out, err = p.communicate()
    print(out)
    out = out.split("\n")
    Master_route = []
    read_now = 0
    for line in out:
        if "LNS" in line:
            read_now = 1
        if "D0-D0" in line and read_now:
            Master_route.append(line)

    # Dis-aggregation
    Real_tours = []
    Total_Cost = 0
    for route in Master_route:
        route = route.split(":")[1]
        route = [inx.split("-")[0].strip() for inx in route.split("->")]
        Tour, Cost = Dis_aggregation(Data, route, TW_indicator)
        Real_tours.append([Cost, Tour])
        Total_Cost += Cost

    Run_time = time.time()-Timer_start
    # Draw the final tours all together
    # Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time)
    # save the CUSTOMERS SEQUENCE
    save_the_customers_sequence(CWD,file_name, Real_tours,Total_Cost,Run_time )
    

if __name__ == "__main__":
    run_aggregation_disaggregation(sys.argv[1:])
