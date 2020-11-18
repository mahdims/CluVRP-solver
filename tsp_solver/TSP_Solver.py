import numpy as np
import sys
import subprocess as sub
import pandas as pd
from tsp_solver import Other_TSP_solvers

def nearest_neighbor(dist_matrix, nodes, start=None):
    # Create a customer sequence by Nearest Neighbor algorithm
    # If  the start is given then the first node in the sequence would be start /
    # otherwise the function selects the first node in the sequence randomly.
    if start:
        path = [start]
        nodes.remove(start)
    else:
        inx = np.random.randint(len(nodes))
        path = [nodes.pop(inx)]

    while nodes:
        inx = dist_matrix[path[-1]][nodes].argmin()
        path.append(nodes.pop(inx))

    return path


def calc_path_dist(dist_matrix, path):
    path_distance = dist_matrix[path[-1]][path[0]]
    for ind in range(len(path) - 1):
        path_distance += dist_matrix[path[ind]][path[ind + 1]]
    return path_distance


def swap(path, swap_first, swap_last):
    path_updated = path[0:swap_first+1] + path[swap_last:-len(path) + swap_first:-1] \
                   + path[swap_last + 1:len(path)]
    return path_updated


def calc_distance_difference(dist_matrix, path, swap_first, swap_last):

    del_dist = dist_matrix[path[swap_first]][path[swap_first+1]] \
               + dist_matrix[path[swap_last]][path[swap_last+1]]
    add_dis = dist_matrix[path[swap_first]][path[swap_last]] \
              + dist_matrix[path[swap_first + 1]][path[swap_last + 1]]

    node = swap_first + 1
    while node != swap_last:
        del_dist += dist_matrix[path[node]][path[node + 1]]
        node += 1

    node = swap_last
    while node != swap_first + 1:
        add_dis += dist_matrix[path[node]][path[node-1]]
        node -= 1

    return add_dis - del_dist


def two_opt_Alg(dist_matrix, Nodes, start=None):
    # This is the 2-opt algorithm
    N = len(Nodes)
    best_route = nearest_neighbor(dist_matrix, list(Nodes.keys()), start)
    best_distance = calc_path_dist(dist_matrix, best_route)

    # print("New cluster")
    noimprove = 0
    while noimprove < 2:
        for swap_first in range(1, N - 2):
            for swap_last in range(swap_first + 1, N - 1):

                dist_diff = calc_distance_difference(dist_matrix, best_route, swap_first, swap_last)

                if dist_diff < 0:
                    best_route = swap(best_route, swap_first, swap_last)
                    best_distance = best_distance + dist_diff
                    # print(best_distance)
                    noimprove = 0

        noimprove += 1

    if best_distance != calc_path_dist(dist_matrix, best_route):
        sys.exit("Negative cost !")
    return best_route, best_distance


def Route_correction(Sequence, start="D0", end="D1"):
    # This function adjust the start and end of the Route.
    # Since we solve a TSP start and end of the Hamiltonion path should be adjusted
    inx_s = np.where(np.array(Sequence) == start)[0][0]
    if inx_s == len(Sequence) - 1:  # when the start of the sequence is at the last position
        if Sequence[0] == end:  # easy the end is at the first just reverse every thing
            Sequence.reverse()
        if Sequence[inx_s - 1] == end:  # 180 degree the opposite of what we need
            Sequence = Sequence[inx_s:] + Sequence[:inx_s]
    else:
        if Sequence[inx_s + 1] == end:
            inx_e = inx_s + 1
            Sequence = Sequence[:inx_e][::-1] + Sequence[inx_e:][::-1]
        if Sequence[inx_s - 1] == end:
            Sequence = Sequence[inx_s:] + Sequence[:inx_s]
    return Sequence


def LKH3(e_ttime, Gnodes):

    # Now we start to build the TSP_in file
    parsed_lines = []
    parsed_lines.append("TYPE: ATSP \n"
                        f"DIMENSION: {len(Gnodes)}\n"
                        "EDGE_WEIGHT_TYPE: EXPLICIT\n"
                        "EDGE_WEIGHT_FORMAT: FULL_MATRIX\n" 
                        "EDGE_WEIGHT_SECTION\n")
    with open("./tsp_solver/LKH/TSP_in.txt", 'w') as out_file:
        out_file.writelines(parsed_lines)
        e_ttime.to_csv(out_file, header=None, index=None, sep=' ', mode='a')
        out_file.write("EOF")

    p = sub.Popen(["./tsp_solver/LKH/LKH", "./tsp_solver/LKH/pr.par"], stdout=sub.PIPE,
                  stderr=sub.PIPE, universal_newlines=True)
    p.wait()
    out, err = p.communicate()
    print(err)

    route = []
    Tour_data = 0
    with open("./tsp_solver/LKH/Tsp_out", "r") as file:
        for line in file:
            if "Length" in line:
                objval = int(line.split("=")[1])
                continue
            if "TOUR_SECTION" in line:
                Tour_data = 1
                continue
            if "EOF" in line:
                Tour_data = 0
                del route[-1]
            if Tour_data:
                route.append(int(line))

    route = [Gnodes[inx - 1] for inx in route]

    return route, objval


def solve(e_ttime, Nodes, start=None, end=None):
    # This function unify the use of tsp solvers
    Gnodes = list(Nodes.keys())
    N = len(Nodes)
    # Create the nice pandas dataframe for distance matrix
    if type(e_ttime).__module__ != pd.__name__:
        np_ttime = np.zeros((len(Nodes), len(Nodes)))
        for inx1, i in enumerate(Gnodes):
            for j in Gnodes[inx1+1:]:
                np_ttime[inx1, Gnodes.index(j)] = e_ttime[(i, j)]
                np_ttime[Gnodes.index(j), inx1] = np_ttime[inx1, Gnodes.index(j)]

    e_ttime = pd.DataFrame(np_ttime, index=Gnodes, columns=Gnodes)

    # route that do not need a tsp to be solved
    if end:

        BigM = e_ttime.values.max()
        e_ttime[start][end] = e_ttime[end][start] = -1 * BigM

        if N <= 3:
            Gnodes.remove(start)
            Gnodes.remove(end)
            if Gnodes:
                customer = Gnodes[0]
                route = [start, customer, end]
                cost = e_ttime[start][customer] + e_ttime[customer][end]
            else:
                route = [start, end]
                cost = e_ttime[start][end]

            return route, cost
    else:
        if N <= 3:
            return Gnodes, sum(sum(e_ttime.values))

    # Make the distances integer
    e_ttime = 10000 * e_ttime
    e_ttime = e_ttime.astype("int32")

    # select the TSP solver
    if 1:
        route, objval = Other_TSP_solvers.TSP_concorde(e_ttime, Gnodes)

        if objval == "Fail":
            # the LKH3 should be downloaded, make and placed in LKH folder
            route, objval = LKH3(e_ttime, Gnodes)
            print("--------------------------------")
            print(objval)
            print("--------------------------------")
    else:
        # Independent implementation of 2-opt
        route, objval = two_opt_Alg(e_ttime, Nodes,)

    objval = objval / 10000

    if end:
        # we are in dis aggregation that solves TSP to find hamiltonian paths
        route = Route_correction(route, start, end)
        objval += BigM


    return route, objval