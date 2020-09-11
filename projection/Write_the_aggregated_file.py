
def Write_the_aggregated_file(Data, CWD, file_name):
    path2file = CWD.replace("solver", "route") + f"/aggregated_data/instances/agg_{file_name}"
    f = open(path2file, "w+")
    f.write("ID\u0009Type\u0009x\u0009y\u0009Demand\u0009Ready\u0009Due\u0009Service\n")
    f.write("D0\u0009d\u0009"+str(Data["depot"].coord[0])+"\u0009"+str(Data["depot"].coord[1]) +
            "\u00090\u0009"+str(Data["depot"].TW[0])+"\u0009"+str(Data["depot"].TW[1])+"\u00090\n")

    for clu in Data["Clusters"].values():
        clu.centroid = list(clu.centroid)
        clu.centroid[0] = round(clu.centroid[0], 0)
        clu.centroid[1] = round(clu.centroid[1], 0)
        clu.demand = round(clu.demand, 0)
        clu.service_time = round(clu.service_time, 0)
        f.write(str(clu.ID) + "\u0009" + "c" + "\u0009" + str(clu.centroid[0]) + "\u0009" + str(clu.centroid[1])
                        + "\u0009" + str(clu.demand) + "\u0009" + str(clu.TW[0]) + "\u0009" + str(clu.TW[1]) + '\u0009'
                        + str(clu.service_time) + "\n")

    # quick solution should be changed after
    max_demand = max([clu.demand for clu in Data["Clusters"].values()])
    f.write("\n")
    f.write("Q battery capacity /%d/\n" % (Data["Q"]) )
    f.write("C vehicle load /%d/\n" % max(Data["C"], max_demand))
    f.write("R replenishment time /%d/" % Data["R"])
    f.close()

    return path2file
