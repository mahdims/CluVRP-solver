import numpy as np
from clustering import Hexogonal

def convert_the_coordinates(x, y, x_origin, y_origin):
    longitude_conversion_coe = 65.0673235 	#KM
    latitude_conversion_coe = 111.206094  #KM
    C_coord = [int(100*(x-x_origin)*longitude_conversion_coe), int(100*(y-y_origin)*latitude_conversion_coe)]
    return C_coord


def XY_range(customers):
    max_x = customers[2].coord[0]
    min_x = customers[2].coord[0]
    max_y = customers[2].coord[1]
    min_y = customers[2].coord[1]
    for cus in customers.values():
        if cus.coord[0] < min_x:
            min_x = cus.coord[0]
        if cus.coord[0] > max_x:
            max_x = cus.coord[0]

        if cus.coord[1] < min_y:
            min_y = cus.coord[1]
        if cus.coord[1] > max_y:
            max_y = cus.coord[1]

    return [min_x, max_x], [min_y, max_y]


class Customer:
    def __init__(self, ID, coord, d, TW=[0,0], ST=0):
        self.ID = ID
        self.coord = coord
        self.demand = d
        self.TW = TW
        self.service_time = ST
        self.clu_id = 0


def read_Li_data(Path_2_file):
    customers = {}
    f = open(Path_2_file, "r")
    lines = list(f)
    depot_flag= 0
    cus_flag = 0
    demand_flag = 0
    f.close()
    for line in lines:
        if "DIMENSION" in line:
            N = int(line.split(":")[1])
        elif "CAPACITY" in line:
            Cap = int(line.split(":")[1])
        elif "NODE_COORD_SECTION" in line:
            depot_flag = 1
            cus_flag = 1
            continue
        elif "DEMAND_SECTION" in line:
            cus_flag = 0
            demand_flag = 1
            continue
        elif "DEPOT_SECTION" in line:
            return depot, Cap, customers

        if depot_flag:
            depot = [float(a) for a in line.split(" ")[1:]]
            depot = Customer("D0", depot, 0)
            depot_flag = 0
            continue

        if cus_flag:
            Id, x, y = [float(a) for a in line.split(" ")]
            customers[Id] = Customer(Id, (x, y), 0)

        if demand_flag:
            Id, d = [int(a) for a in line.split(" ")]
            if Id != 1:
                customers[Id].demand = d

    return depot, Cap, customers


def read_Arnold_data(Path_2_file):
    f = open(Path_2_file, "r")
    lines = list(f)
    N = int(lines[3].split(":")[1])
    Cap = int(lines[5].split(":")[1])
    f.close()
    depot = lines[7: 8]
    depot = [float(a) for a in depot[0].split("\t")[1:]]
    depot = Customer("D0", depot, 0)
    customers_coord = lines[8: 8+N-1]
    customers_demand = lines[8+N+1:8+2*N]
    customers = {}
    for line_inx, cust in enumerate(customers_coord):

        Id, x, y = [float(a) for a in cust.split("\t")]
        demand = int(customers_demand[line_inx].split("\t")[1])
        customers[Id] = Customer(Id, (x,y), demand)

    return depot, Cap, customers


def read_clu_data(Path_2_file):
    f = open(Path_2_file, "r")
    lines = list(f)
    f.close()
    customers = {}
    clusters = {}
    depot_flag = 0
    cus_flag = 0
    clu_flag = 0
    demand_flag = 0
    M = 0
    for line in lines:
        if "DIMENSION" in line:
            N = int(line.split(":")[1])
        elif "CAPACITY" in line:
            Cap = int(line.split(":")[1])

        elif "VEHICLES" in line:
            M = int(line.split(":")[1])

        elif "NODE_COORD_SECTION" in line:
            depot_flag = 1
            cus_flag = 1
            continue
        elif "GVRP_SET_SECTION" in line:
            clu_flag = 1
            cus_flag = 0
            continue
        elif "DEMAND_SECTION" in line:
            clu_flag = 0
            demand_flag = 1
            continue
        elif "INTRA_CLUSTER_DISTANCE" in line:
            return M, depot, Cap, customers, clusters

        if depot_flag:
            depot = [float(a) for a in line.split(" ")[1:] if a]
            depot = Customer("D0", depot, 0)
            depot_flag = 0
            continue

        if cus_flag:
            Id, x, y = [float(a) for a in line.split(" ") if a ]
            Id = int(Id)
            customers[Id] = Customer(Id, (x, y), 0)

        if clu_flag:
            cus_list = line.split(" ")[1:]
            Id = int(cus_list[0])
            new_cluster = Hexogonal.Cluster(Id)
            for cus in cus_list[1:-1]:
                if cus:
                    cus = int(cus)
                    customers[cus].clu_id = Id
                    new_cluster.customers[cus] = customers[cus]

            clusters[Id] = new_cluster

        if demand_flag:
            Id, d = [int(a) for a in line.split(" ")[:-1] if a]
            clusters[Id].demand = d

    return M, depot, Cap, customers, clusters


def read_the_data(Path_2_file, path_2_dis_mat=None):
    clean_data = {}
    if "Clu" in Path_2_file:
        M, depot, Cap, customers, clusters = read_clu_data(Path_2_file)
        clean_data["Clusters"] = clusters
    else:
        if "Arnold" in Path_2_file:
            depot, Cap, customers = read_Arnold_data(Path_2_file)
        elif"Li" in Path_2_file:
            depot, Cap, customers = read_Li_data(Path_2_file)

        clean_data["Clusters"] = {}

    x_range, y_range = XY_range(customers)
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

        clean_data["Full_dis"] = Full_dis
        clean_data["Full_consump"] = Full_consump

    clean_data["depot"] = depot
    clean_data["Vehicles"] = M
    clean_data["Aux_depot"] = Customer("D1", depot.coord, 0)
    clean_data["Customers"] = customers
    clean_data["C"] = Cap
    clean_data["X_range"] = x_range
    clean_data["Y_range"] = y_range

    return clean_data



def read_vrp_data(Path_2_file, M):
    clean_data = {}
    customers = {}
    f = open(Path_2_file, "r")
    lines = list(f)
    depot_flag = 0
    cus_flag = 0
    demand_flag = 0
    f.close()
    for line in lines:
        if "DIMENSION" in line:
            N = int(line.split(":")[1])
        elif "CAPACITY" in line:
            Cap = int(line.split(":")[1])
        elif "NODE_COORD_SECTION" in line:
            depot_flag = 1
            cus_flag = 1
            continue
        elif "DEMAND_SECTION" in line:
            cus_flag = 0
            demand_flag = 1
            continue
        elif "DEPOT_SECTION" in line:
            clean_data["depot"] = depot
            clean_data["Vehicles"] = M
            clean_data["Aux_depot"] = Customer("D1", depot.coord, 0)
            clean_data["Clusters"] = customers
            clean_data["C"] = Cap

            return clean_data

        if depot_flag:
            depot = [float(a) for a in line.split(" ")[1:]]
            depot = Customer("D0", depot, 0)
            depot_flag = 0
            continue

        if cus_flag:
            Id, x, y = [float(a) for a in line.split(" ")]
            customers[Id] = Customer(Id, (x, y), 0)

        if demand_flag:
            Id, d = [int(a) for a in line.split(" ")]
            if Id != 1:
                customers[Id].demand = d



