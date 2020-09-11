
import numpy as np

def plot_out(ax , clean_data, Real_tours,Cost,Time):
    C_coord = np.array(list(clean_data["C_coord"].values()))
    S_coord = np.array(list(clean_data["S_coord"].values()))
    # draw the customer and station points on the 100*100 plate
    ax.set_aspect('equal')
    ax.scatter(*clean_data["depot"].coord,marker=',',c="k" ,   s=80 )
    ax.scatter(C_coord[:,0],C_coord[:,1],marker ="o",c="g")
    if S_coord:
        ax.scatter(S_coord[:,0],S_coord[:,1],marker="o", c="r")
    ax.axis([0,100,0,100])
    #ax.xlabel("X")
    #ax.ylabel("Y")
    # draw a rectangular round each cluster
    for clster in clean_data["Clusters"].values():
        #print(clster.rectangular_H)
        #rec = Rectangle(clster.rectangular_orgin, height =clster.rectangular_H, width =clster.rectangular_W,
        #                    facecolor="green", alpha=0.2, edgecolor='k')
        #ax.add_patch(rec)
        #ax.scatter(clster.center[0], clster.center[1] , marker='o',c="b" ,   s=50)
        #ax.scatter(*clster.centroid, marker='*', c="b", s=50)
        ax.add_patch(clster.Drawing())
        if len(clster.centroid):
            ax.text(*clster.centroid, s= clster.ID,fontsize=12)
        #dump = np.array(clster.Enter_exit_points.values())
        #ax.scatter(dump[:,0], dump[:,1], marker="o", c="b" , s=20)
        #ax.scatter(*clster.corners["up_w"], marker="o", c="b", s=20)

    # Draw the real tour for aggregation method
    for route in Real_tours:
        start = clean_data["depot"].coord
        for next_node in route[1:-1]:
            end = clean_data["Customers"][next_node].coord
            ax.plot((start[0],end[0]), (start[1],end[1]), color='k', linestyle='-', linewidth=0.5)
            start = clean_data["Customers"][next_node].coord
        end = clean_data["depot"].coord
        ax.plot((start[0], end[0]), (start[1], end[1]), color='k', linestyle='-', linewidth=0.5)

    # write the cost and execution time
    ax.text(30, -12, "Total traveling time : %s \n Execution time : %s" %( round(Cost,1) , round(Time,2) ) , fontsize = 13.0)



