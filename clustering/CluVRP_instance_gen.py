import glob
import heapq
import pickle
import time
import sys
sys.path.append("/home/mahdi/Google Drive/PostDoc/Scale vehicle routing/Code - git/VRP-aggregation")

from utils import read, write
from utils import Plots, Distance
from clustering import Exposito_Clustering


def truncated_dis_matrix(Data, file):
    dist = {}
    start = time.time()
    for cus in Data["Customers"].values():
        dis_to_depot = Distance.euclidean_dis(Data['depot'].coord, cus.coord)
        new_h = [(dis_to_depot,0)]
        heapq.heapify(new_h)
        for other_cus in Data["Customers"].values():
            if other_cus != cus:
                dis_to_other = Distance.euclidean_dis(cus.coord, other_cus.coord)
                if len(new_h) < 100:
                    heapq.heappush(new_h, (dis_to_other, other_cus.ID))
                else:
                    heapq.heappushpop(new_h, (dis_to_other, other_cus.ID))

        dist[cus.ID] = new_h

    dist["time"] = time.time() - start
    file =file.replace(".txt", "")
    write.pickle_dump(dist, f"{file}_dist_mat")


if __name__ == "__main__":
    file_names = glob.glob("data/Arnold/*.txt")
    for file in ["data/Arnold/Brussels2.txt"]:#file_names:
        file_simple_name = file.split("/")[-1].replace(".txt", "")
        print(f"We are solving {file_simple_name}")
        Data = read.read_the_data(file)
        truncated_dis_matrix(Data,file)

        with open(f"data/Arnold/{file_simple_name}_dist_mat", "rb") as distance_matrix:
            Data["Full_dis"] = pickle.load(distance_matrix)

        # Data = Exposito_Clustering.Exposito_Clustering(Data)
        # Plots.Draw_on_a_plane(Data, [], 0, 0)





