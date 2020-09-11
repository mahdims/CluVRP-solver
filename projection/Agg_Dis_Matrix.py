# This script write the distance and consumption matrix .txt file for aggregated customers (clusters).
# The output file is in the VRP-solver format.
import itertools as it


def find_cluster(Node_Id, Clusters):
    if Node_Id == "D0":
        return "D0"

    for clu in Clusters.values():
        if clu.Is_node_here(Node_Id):
            return str(clu.ID)


def Find_the_intra_cluster_arc(Data, clu1, clu2):
    if clu1.ID == "D0":
        end_points1 = ["D0"]
    else:
        end_points1 = clu1.HC_sequence[0], clu1.HC_sequence[-1]

    if clu2.ID == "D0":
        end_points2 = ["D0"]
    else:
        end_points2 = clu2.HC_sequence[0], clu2.HC_sequence[-1]

    intra_arc_list = [[(a,b), Data["Full_dis"][a,b]] for a,b in it.product(end_points1,end_points2)]
    min_arc, min_dis = min (intra_arc_list, key=lambda x:x[1])

    return min_arc, min_dis


def update_dis_mat(Data, CWD, filename):
    dis_mat_path = CWD.replace("solver", "route") + f"/aggregated_data/distance_matrix/agg_{filename}"
    file = open(dis_mat_path, "w+")
    Clusters_ID = list(Data["Clusters"].values()) + [Data["depot"]]
    for clu1, clu2 in it.combinations(Clusters_ID, 2):
        for a, b in [(clu1, clu2), (clu2, clu1)]:
            min_arc, min_dis = Find_the_intra_cluster_arc(Data, a, b)
            # print(a.ID,b.ID,min_dis)
            file.write("Link\n%s %s \n" % (a.ID, b.ID))
            file.write("1\n0 \u0009" + str(Data["depot"].TW[1]) + "\u0009 0\u0009  %s\n" % (int(min_dis * 1000)))
            file.write("1\n0 \u0009" + str(Data["depot"].TW[1]) + "\u0009 0\u0009  %s\n" % (
                int(Data["Full_consump"][min_arc] * 1000)))

    file.close()

    return dis_mat_path
