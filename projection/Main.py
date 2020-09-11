from read import read_the_data , Honeycomb_Clustering
from Direct_VRP import Direct_VRP
from Plots import plot_out
from Cluster_routing import Cluster_routing
from Cluster_routing_min_dis import Cluster_routing_min_dis
from Dis_aggregation1 import Dis_aggregation1
from Dis_aggregation2 import Dis_aggregation2
import matplotlib.pyplot as plt
import time
from Cluster_routing_min_dis import Cluster_routing_min_dis
# Calculating the distance matrix is de-centeralized !! but it can be calculate once


folder = "0"
file_name = "c101_0"
Data = read_the_data(folder, file_name)
Data = Honeycomb_Clustering(Data)

# Solve with the aggrigation (Centroid to centroid approch)
Starting_time = time.time()
Master_Tours = Cluster_routing_min_dis(Data)
#Master_Tours = Cluster_routing(Data)
Real_tours = []
Total_Cost = 0
for M_path in Master_Tours:
    Tour, Cost = Dis_aggregation2(Data, M_path)
    Real_tours.append(Tour)
    Total_Cost += Cost

Exe_time_aggregation = time.time() - Starting_time
print(Exe_time_aggregation , Total_Cost)

# Solve with the direct VRP
Starting_time = time.time()
Opt_tours, Opt_cost = Direct_VRP(Data)
Exe_time_direct =  time.time() - Starting_time

#print(Exe_time_direct , Opt_cost)

fig, ax = plt.subplots(1, 2)
# aggregation solution
ax[0].set_title("Solution provided by CA22",fontsize = 13.0)
plot_out(ax[0], Data, Real_tours , Total_Cost ,Exe_time_aggregation)
# Direct solution
ax[1].set_title("Optimal solution",fontsize = 13.0)
plot_out(ax[1], Data, Opt_tours,Opt_cost,Exe_time_direct)
plt.show()