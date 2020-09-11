import numpy as np
import pandas as pd


def convert_the_coordinates(x, y, x_origin, y_origin):
    longitude_conversion_coe = 65.0673235 	#KM
    latitude_conversion_coe = 111.206094  #KM
    C_coord = [int(100*(x-x_origin)*longitude_conversion_coe), int(100*(y-y_origin)*latitude_conversion_coe)]
    return C_coord


class Customer:
    def __init__(self, ID, coord, d, TW, ST):
        self.ID = ID
        self.coord = coord
        self.demand = d
        self.TW = TW
        self.service_time = ST


def read_the_data(Path_2_file, path_2_dis_mat = None):
    np.random.seed(0)
    f = open(Path_2_file, "r")
    lines = list(f)
    Q = int(lines[-3].split("/")[1])
    C = int(lines[-2].split("/")[1])
    R = int(lines[-1].split("/")[1])
    f.close()
    data = pd.read_csv(Path_2_file, sep="\t", skipfooter=4, engine='python')
    data.columns = ["ID", "Type",	"x",	"y",	"Demand",	"Ready",	"Due",	"Service"]
    clean_data = {}
    stations_coord = {}
    customers_coord = {}
    customers = {}
    counter = 1
    max_x = max(data["x"])
    min_x = min(data["x"])
    max_y = max(data["y"])
    min_y = min(data["y"])
    max_x, max_y = convert_the_coordinates(max_x, max_y, min_x, min_y)
    for inx, s in enumerate(data["Type"]):
        # Convert to cartesian coordinates
        coord = convert_the_coordinates(data["x"][inx], data["y"][inx], min_x, min_y)
        if "d" in s:
            depot = Customer("D0", coord, data["Demand"][inx],
                                         (data["Ready"][inx], data["Due"][inx]), data["Service"][inx])
        elif "f" in s:
            stations_coord[inx] = coord
        else:
            customers_coord[inx] = coord
            cus_ID = data["ID"][inx]
            customers[cus_ID] = Customer(cus_ID, coord, data["Demand"][inx],
                     (data["Ready"][inx], data["Due"][inx]),data["Service"][inx])

    # read the distance matrix file
    if path_2_dis_mat:
        file = open(path_2_dis_mat)
        lines = list(file)
        file.close()
        Full_dis = {}
        Full_consump = {}
        for line_inx in range(0, len(lines), 6):
            arc = tuple(lines[line_inx + 1].replace("\n", "").split(" "))
            Full_dis[arc] = int(lines[line_inx + 3].replace("\n", "").split("\t")[3]) / 1000
            Full_consump[arc] = int(lines[line_inx + 5].replace("\n", "").split("\t")[3]) / 1000

    customers_No = len(customers_coord)
    clean_data["Full_dis"] = Full_dis
    clean_data["Full_consump"] = Full_consump
    clean_data["depot"] = depot
    clean_data["S_coord"] = stations_coord
    clean_data["C_coord"] = customers_coord
    clean_data["Customers"] = customers
    clean_data["N_C"] = customers_No
    clean_data["Demand"] = data["Demand"]
    clean_data["Clusters"] = {}
    clean_data["Q"] = Q
    clean_data["C"] = C
    clean_data["R"] = R
    clean_data["Axu_depot"] = max(customers_coord.keys()) + 1
    clean_data["X_range"] = (min_x, max_x)
    clean_data["Y_range"] = (min_y, max_y)
    # erase this after test
    # clean_data["depot"].TW = (0, 23000)
    return clean_data



'''
def K_means_Clustering(clean_data):
    customers_x = clean_data["Cx"]
    customers_y = clean_data["Cy"]
    # create kmeans object
    N_of_clusters = 10
    kmeans = KMeans(n_clusters=N_of_clusters)
    # fit kmeans object to data
    kmeans.fit(zip(customers_x.values(),customers_y.values()))
    # save new clusters for chart
    y_km = kmeans.fit_predict(zip(customers_x.values(),customers_y.values()))

    for cl in range(N_of_clusters):
        Clu = 0
        Clu.K_mean_center =  kmeans.cluster_centers_[cl]
        clean_data["Clusters"].append(Clu)

    return clean_data
'''
