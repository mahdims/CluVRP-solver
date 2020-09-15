import itertools as it


def Write_AggInstance(path2file,Data):
    original_name = path2file.split("/")[-1]
    path2file = path2file.replace(original_name, f"agg_data/Agg_{original_name}")
    f = open(path2file, "w+")
    f.write("ID\u0009Type\u0009x\u0009y\u0009Demand\u0009Ready\u0009Due\u0009Service\n")
    f.write("D0\u0009d\u0009"+str(Data["depot"].coord[0])+"\u0009"+str(Data["depot"].coord[1]) +
            "\u00090\u0009"+str(Data["depot"].TW[0])+"\u0009"+str(Data["depot"].TW[1])+"\u00090\n")

    for clu in Data["Clusters"].values():
        clu.reference = list(clu.reference)
        clu.reference[0] = round(clu.reference[0], 0)
        clu.reference[1] = round(clu.reference[1], 0)
        clu.demand = round(clu.demand, 0)
        clu.service_time = round(clu.service_time, 0)
        f.write(str(clu.ID) + "\u0009" + "c" + "\u0009" + str(clu.reference[0]) + "\u0009" + str(clu.reference[1])
                        + "\u0009" + str(clu.demand) + "\u0009" + str(clu.TW[0]) + "\u0009" + str(clu.TW[1]) + '\u0009'
                        + str(clu.service_time) + "\n")

    f.write("\n")
    f.write("Q battery capacity /%d/\n" % Data["C"] )
    f.write("C vehicle load /%d/\n" % Data["C"])
    f.write("R replenishment time /%d/" % Data["C"])
    f.close()

    return path2file


def Write_AggDis_mat(Data,path2file, clu_dis):
    original_name = path2file.split("/")[-1]
    dis_mat_path = path2file.replace(original_name, f"agg_data/AggDis_{original_name}")
    file = open(dis_mat_path, "w")
    for clu1, clu2 in clu_dis.keys():

        file.write("Link\n%s %s \n" % (clu1, clu2))
        file.write("1\n0 \u0009" + str(Data["depot"].TW[1]) + "\u0009 0\u0009  %s\n" % (int(clu_dis[clu1,clu2] * 1000)))
        file.write("1\n0 \u0009" + str(Data["depot"].TW[1]) + "\u0009 0\u0009  %s\n" % (
            int(clu_dis[clu1,clu2] * 1000)))

    file.close()

    return dis_mat_path


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