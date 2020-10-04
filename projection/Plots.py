import numpy as np
import matplotlib.pyplot as plt
import Hexogonal


def Draw_on_a_plane(Data, Real_tours, Total_Cost, Run_time):
    fig, ax = plt.subplots(1)
    # aggregation solution
    ax.set_title("Aggregation Solution", fontsize=13.0)
    plot_out(ax, Data, Real_tours, Total_Cost, Run_time)
    plt.show()


def plot_out(ax, Data, Real_tours, Cost, Time):
    ax.axis([Data["X_range"][0]-10, Data["X_range"][1]+10, Data["Y_range"][0]-10, Data["Y_range"][1]+10])
    # draw the station points on the plate
    ax.set_aspect('equal')
    ax.scatter(*Data["depot"].coord, marker=',', c="k", s=80)

    # draw clusters
    for cluster in Data["Clusters"].values():
        if type(cluster) == Hexogonal.Hexo:
            ax.add_patch(cluster.Drawing())
        cus_coord = np.array([cus.coord for cus in cluster.customers.values()])
        ax.scatter(cus_coord[:, 0], cus_coord[:, 1])
        ax.text(*cluster.reference, s=cluster.ID, fontsize=12)

    # Draw the real tour for aggregation method
    for route in Real_tours:
        start = Data["Customers"][route[1][1]].coord
        for next_node in route[1][2:-1]:
            end = Data["Customers"][next_node].coord
            ax.plot((start[0], end[0]), (start[1], end[1]), color='k', linestyle='-', linewidth=0.5)
            start = Data["Customers"][next_node].coord
    # write the cost and execution time
    ax.text(sum(Data["X_range"])/2, -20, "Total traveling time : %s \n Execution time : %s" %(round(Cost, 1), round(Time, 2)), fontsize=13.0)
