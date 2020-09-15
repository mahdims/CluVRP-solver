import numpy as np
import matplotlib.pyplot as plt



def Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time):
    fig, ax = plt.subplots(1)
    # aggregation solution
    ax.set_title("Aggregation Solution", fontsize=13.0)
    plot_out(ax, Data, Real_tours, Total_Cost, Run_time)
    plt.show()


def plot_out(ax, clean_data, Real_tours,Cost,Time):
    ax.axis([*clean_data["X_range"], *clean_data["Y_range"]])
    S_coord = np.array(list(clean_data["S_coord"].values()))
    # draw the station points on the plate
    ax.set_aspect('equal')
    ax.scatter(*clean_data["depot"].coord,marker=',',c="k" ,   s=80 )
    if len(S_coord) != 0:
        ax.scatter(S_coord[:,0],S_coord[:,1],marker="o", c="r")
    # draw a rectangular round each cluster
    for cluster in clean_data["Clusters"].values():
        ax.add_patch(cluster.Drawing())
        cus_coord = np.array([cus.coord for cus in cluster.customers.values()])
        ax.scatter(cus_coord[:, 0], cus_coord[:, 1])
        ax.text(*cluster.centroid, s= cluster.ID,fontsize=12)
        #dump = np.array(clster.Enter_exit_points.values())
        #ax.scatter(dump[:,0], dump[:,1], marker="o", c="b" , s=20)
        #ax.scatter(*clster.corners["up_w"], marker="o", c="b", s=20)

    # Draw the real tour for aggregation method
    for route in Real_tours:
        start = clean_data["depot"].coord
        for next_node in route[1][1:-1]:
            end = clean_data["Customers"][next_node].coord
            ax.plot((start[0],end[0]), (start[1],end[1]), color='k', linestyle='-', linewidth=0.5)
            start = clean_data["Customers"][next_node].coord
        end = clean_data["depot"].coord
        ax.plot((start[0], end[0]), (start[1], end[1]), color='k', linestyle='-', linewidth=0.5)

    # write the cost and execution time
    ax.text(sum(clean_data["X_range"])/2, -20, "Total traveling time : %s \n Execution time : %s" %( round(Cost,1) , round(Time,2) ) , fontsize = 13.0)
