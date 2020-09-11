
def find_cluster(Node_Id, Clusters):
    if Node_Id == "D0":
        return "D0"

    for clu in Clusters.values():
        if clu.Is_node_here(Node_Id):
            return str(clu.ID)


def update_dis_mat(Data, filename):

    dis_dic = {}

    for arc, distance in Data["Full_dis"].items():

        intra_arc = (find_cluster(arc[0], Data["Clusters"]),find_cluster(arc[1], Data["Clusters"]))
        if intra_arc in dis_dic.keys():
            dis_dic[intra_arc].append((arc,distance))
        else:
            dis_dic[intra_arc] = [(arc,distance)]

    file = open("%s_agg.txt" % filename, "w+")
    for key, val in dis_dic.items():

        min_arc, min_dis = min(val, key=lambda x: x[1])
        dis_dic[key] = [min_arc, min_dis]
        key = list(key)
        for a, b in [key, key[::-1]]:
            file.write("Link\n%s %s \n" % (a, b))
            file.write("1\n0 \u0009"+ str(Data["depot"].TW[1]) +"\u0009 0\u0009  %s\n" % (min_dis * 1000))
            file.write("1\n0 \u0009"+ str(Data["depot"].TW[1]) +"\u0009 0\u0009  %s\n" % (Data["Full_consump"][min_arc] * 1000))

    file.close()

    return "%s_agg" % filename


