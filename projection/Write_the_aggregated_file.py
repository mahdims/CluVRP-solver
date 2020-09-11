
def Write_the_aggregated_file(File_name, Data):

    f = open("%s.txt" % File_name, "w+")
    f.write("ID\u0009"+"Type" + "\u0009" + "x" + "\u0009" + "y" + "\u0009" + "Demand" + "\u0009" + "Ready" + "\u0009" + "Due" + "\u0009" + "Service" +"\n")
    f.write("D0\u0009d\u0009" + str(Data["depot"].coord[0])+"\u0009"+str(Data["depot"].coord[1])+"\u0009"+ "0" +"\u0009"+
            str(Data["depot"].TW[0])+"\u0009"+str(Data["depot"].TW[1])+"\u0009"+"0"+"\n")

    for clu in Data["Clusters"].values():
        clu.centroid = list(clu.centroid)
        clu.centroid[0] = round(clu.centroid[0], 0)
        clu.centroid[1] = round(clu.centroid[1], 0)
        clu.demand = round(clu.demand, 0)
        #if clu.service_time > 700:
        #    clu.service_time = 700
        clu.service_time = round(clu.service_time, 0)
        f.write(str(clu.ID) + "\u0009" + "c" + "\u0009" + str(clu.centroid[0]) + "\u0009" + str(clu.centroid[1])
                     + "\u0009" + str(clu.demand) + "\u0009" + str(clu.TW[0]) + "\u0009" + str(clu.TW[1]) + '\u0009' + str(clu.service_time)
                + "\n")

    f.write("\n")
    f.write("Q battery capacity /%d/\n" % Data["Q"] )
    f.write("C vehicle load /%d/\n" % Data["C"])
    f.write("R replenishment time /%d/" % Data["R"])
    f.close()
