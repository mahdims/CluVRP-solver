import subprocess as sub
import os
import time
import matplotlib.pyplot as plt
from read import read_the_data , Honeycomb_Clustering
from Agg_Dis_Matrix import update_dis_mat
from Write_the_aggregated_file import Write_the_aggregated_file
from Dis_aggregation1 import Dis_aggregation1
from Plots import plot_out
# current directory path
dir_path = os.path.dirname(os.path.realpath(__file__))
# Problem specification
folder = "0"
file_name = "c101_0"
Dis_mat_name = "c1_Solomon"
Timer_start = time.time()
# read the data from  the text file
Data = read_the_data(folder, file_name,Dis_mat_name)
# Implement the honeycomb clustering
Data = Honeycomb_Clustering(Data)
# compute and write the aggregated distance/consumption file for VRP solver
Dis_mat_name = update_dis_mat(Data,Dis_mat_name)
# write the aggregated input file for VRP solver
Write_the_aggregated_file(file_name, Data)

# Run the VRP solver
p = sub.Popen(["./TDRRRPOptimiser", "%s.txt" %file_name, "%s.txt" %Dis_mat_name], stdout=sub.PIPE, stderr=sub.PIPE,
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
    Tour, Cost = Dis_aggregation1(Data, route)
    Real_tours.append(Tour)
    Total_Cost += Cost


fig, ax = plt.subplots(1)
# aggregation solution
ax.set_title("Aggregation Solution", fontsize=13.0)
plot_out(ax, Data, Real_tours, Total_Cost, time.time()-Timer_start)
plt.show()


#midoutput = open(dir_path+"/%s_agg_sol.txt" %file_name,'w+')
#for l in p.stdout.read():
#    midoutput.write(l)
#midoutput.close()
