import time
import random as rn
import sys
import pickle
import copy
import itertools as it
import math
from utils import read
import os
from collections import deque


class Tour:
    Data = None
    Dis = None

    def __init__(self, seq):
        self.seq = seq
        self.cost = 0
        self.demand = 0

    def __getitem__(self, item):
        return self.seq[item]

    def __len__(self):
        return len(self.seq)

    def __repr__(self):
        return f"Cost : {self.cost} | {self.seq}"

    def __deepcopy__(self, memo):
        id_self = id(self)  # memoization avoids unnecesary recursion
        _copy = memo.get(id_self)
        if _copy is None:
            _copy = type(self)(
                copy.deepcopy(self.seq, memo))
            _copy.calc_demand()
            _copy.calc_cost()
            memo[id_self] = _copy
        return _copy

    def calc_demand(self):
        self.demand = sum(Tour.Data["Clusters"][clu].demand for clu in self[1:-1])

    def calc_cost(self):
        cost = 0
        current = self.seq[0]
        for next in self.seq[1:]:
            cost += Tour.Dis[current, next]
            if next != "D0":
                cost += Tour.Data["Clusters"][next].service_time
            current = next
        self.cost = cost
        return cost

    def insertion_cost(self, node, pos):
        cost_change = Tour.Dis[self[pos], node] + Tour.Dis[node, self[pos+1]] - Tour.Dis[self[pos], self[pos+1]] \
                      + Tour.Data["Clusters"][node].service_time
        return cost_change

    def insert(self, node, pos):
        self.cost += self.insertion_cost(node, pos)
        self.seq.insert(pos+1, node)
        self.demand += Tour.Data["Clusters"][node].demand

    def remove(self, node):
        inx = self.seq.index(node)
        if inx != 0 or inx != len(self)-1:
            if len(self) > 3:
                self.cost += -Tour.Dis[self[inx-1], self[inx]] - Tour.Dis[self[inx], self[inx+1]] + Tour.Dis[self[inx-1], self[inx+1]] \
                             - Tour.Data["Clusters"][node].service_time
            else:
                self.cost = 0
            self.demand -= Tour.Data["Clusters"][node].demand
        else:
            sys.exit("Try to remove the depot from tour")
        self.seq.remove(node)

    def random_select(self):
        return rn.choice(self.seq[1:-1])

    def without_depot(self):
        temp_seq = copy.deepcopy(self.seq)
        temp_seq.remove("D0")
        temp_seq.remove("D0")
        return temp_seq


def savings_callback(unrouted, i, D):
    savings = [(D[i, "D0"] + D["D0", j] - D[i, j], -D[i, j], i, j) for j in unrouted if i != j]
    savings.sort()
    return savings


def Savings_Alg(Data, Dis, V_c):
    C = Data["C"]
    demand = {clu.ID: clu.demand for clu in Data["Clusters"].values()}
    """
    Implementation of the Webb (1964) sequential savings algorithm /
    construciton heuristic for capaciated vehicle routing problems with
    symmetric distances.
    Webb, M. (1964). A study in transport routing. Glass Technology, 5:178181
    """
    unrouted = copy.copy(V_c)
    # Generate a list of seed nodes for emerging route inititialization
    # build a ordered priority queue of potential route initialization nodes
    seed_customers = copy.copy(V_c)
    seed_customers.sort(reverse=True, key=lambda i: (Dis["D0", i], i))
    # Initialize a single emerging route and make all feasible merges on it
    tours = []

    while unrouted:
        # start a new route
        while True:
            seed = seed_customers.pop()
            if seed in unrouted:
                break

        emerging_route_nodes = deque([seed])
        unrouted.remove(seed)

        route_d = demand[seed]

        savings = savings_callback(unrouted, seed, Dis)

        while len(savings) > 0:
            # Note: i is the one to merge with, and j is the merge_candidate
            best_saving, _, i, j = savings.pop()

            cw_saving = Dis[i, "D0"] + Dis["D0", j] - Dis[i, j]
            if cw_saving < 0.0:
                savings = []  # force route change
                break

            if not j in unrouted:
                continue

            if C and route_d + demand[j] - 1e-10 > C:
                continue  # next savings

            # it is still a valid merge?
            do_left_merge = emerging_route_nodes[0] == i
            do_right_merge = emerging_route_nodes[-1] == i and \
                             len(emerging_route_nodes) > 1
            if not (do_left_merge or do_right_merge):
                # "Reject merge because the %d" % i "is no longer next to the depot.")
                continue  # next savings

            if C:
                route_d += demand[j]

            if do_left_merge:
                emerging_route_nodes.appendleft(j)
            if do_right_merge:
                emerging_route_nodes.append(j)
            unrouted.remove(j)

            # update the savings list
            savings += savings_callback(unrouted, j, Dis)
            savings.sort()

        # All savings merges tested, complete the route
        tour_obj = Tour(["D0"] + list(emerging_route_nodes)+["D0"])
        tour_obj.calc_demand()
        tour_obj.calc_cost()
        tours.append(tour_obj)
        emerging_route_nodes = None

    return tours


def Random_removal(destroyed_tours, un_routed, N_remove):
    # remove some nodes completely randomly from tours
    # Time complexity : O(n)
    while len(un_routed) < N_remove:
        tour_inx = rn.randint(0, len(destroyed_tours)-1)
        tour = destroyed_tours[tour_inx]
        if len(tour) <= 2:
            continue
        visit = rn.randint(1, len(tour)-2)
        un_routed.append(tour[visit])
        tour.remove(tour[visit])

    return destroyed_tours, un_routed


def Route_removal(destroyed_tours, un_routed, M):
    if M:
        while len(destroyed_tours) > M:
            inx = rn.randint(0, len(destroyed_tours))
            un_routed += destroyed_tours[inx].without_depot()
            del destroyed_tours[inx]

    return destroyed_tours, un_routed


def Shaw_next(r, tours):
    # used in Shaw removal to find the next node to remove
    relatedness = {}
    for inx, tour in enumerate(tours):
        for node in tour[1:-1]:
            relatedness[(inx, node)] = Tour.Data["Clusters"][r].demand - \
                                Tour.Data["Clusters"][node].demand +\
                                Tour.Dis[r, node]

    relatedness = sorted(relatedness.items(), key=lambda x:x[0], reverse=True)
    removed = rn.randint(0, int(len(relatedness)/3))
    return relatedness[removed][0]


def Shaw_removal(destroyed_tours, un_routed, N_remove):
    # Ropke and Pisinger () and Shaw (1998) | The general idea is to remove customers that are somewhat similar.
    # It is expected to be reasonably easy to reshuffle similar customers and create new, perhaps better solutions.
    # Relatedness measure :
    # Time complexity : O(n**2)
    # Step1: randomly select a customer, remove and add it to un_routed customers
    # Step2: select r randomly from un_routed
    # step3: sort the customers in routed according to the relatedness to r
    # Step4: select one, remove from routed and add to unrouted, back to 2

    while len(un_routed) < N_remove:
        if un_routed:
            r = rn.choice(un_routed)
        else:
            tour_inx = rn.randint(0, len(destroyed_tours)-1)
            r = destroyed_tours[tour_inx].random_select()
            destroyed_tours[tour_inx].remove(r)
            un_routed.append(r)

        removed = Shaw_next(r, destroyed_tours)
        destroyed_tours[removed[0]].remove(removed[1])
        un_routed.append(removed[1])

    return destroyed_tours, un_routed


def update_removal_benefit(removal_benefit, removed, tour):
    # update the removal benefit list
    # NOTE this should be run before removing the node from tour
    del removal_benefit[removed]
    tinx, node = removed
    ninx = tour.seq.index(node)
    if ninx-1 != 0:
        removal_benefit[(tinx, tour[ninx-1])] += - Tour.Dis[tour[ninx -1], node] \
                                           + Tour.Dis[tour[ninx-1], tour[ninx+1]]
    else:
        pass

    if ninx+1 != len(tour)-1:
        removal_benefit[(tinx, tour[ninx + 1])] += - Tour.Dis[node, tour[ninx+1]] \
                                            + Tour.Dis[tour[ninx-1], tour[ninx+1]]
    else:
        pass

    return removal_benefit


def Worst_removal(destroyed_tours, un_routed, N_remove):
    #  Remove customers with a high cost in the current solution and attempt to insert them in better positions.
    # Cost(i) : current cost - cost of solution after removing i
    # Time complexity : O(n**2)
    # Step 1: sorts the customers according to Cost(i)
    # Step 2: chooses one to be removed,
    # Step 3: recalculate Cost(i), for the remaining customers, and go back to Step 1
    removal_benefit = {}
    for tinx, tour in enumerate(destroyed_tours):
        for ninx in range(1, len(tour)-1):
            removal_benefit[(tinx, tour[ninx])] = Tour.Dis[tour[ninx-1], tour[ninx]] + \
                                    Tour.Dis[tour[ninx], tour[ninx+1]] +\
                                    Tour.Data["Clusters"][tour[ninx]].service_time \
                                    - Tour.Dis[tour[ninx-1], tour[ninx+1]]

    while len(un_routed) < N_remove:
        sorted_benefit = sorted(removal_benefit.items(), key=lambda x: x[1], reverse=True)
        removed = sorted_benefit[rn.randint(0, int(len(sorted_benefit)/3))][0]

        # update the benefit dict
        removal_benefit = update_removal_benefit(removal_benefit,
                                                 removed, destroyed_tours[removed[0]])

        destroyed_tours[removed[0]].remove(removed[1])
        un_routed.append(removed[1])

    return destroyed_tours, un_routed


def Neighbor_graph_removal(destroyed_tours, un_routed, N_remove):
    #
    # Time complexity : O(n)

    return destroyed_tours, un_routed


def Greedy_insertion(Data, tours, un_routed):
    # best possible place to insert
    # this insertion heuristic respects the order of the customers in unrouated
    # Worst time complexity O(n**2)
    M = Data["Vehicles"]
    unable_2_route = []
    for node in un_routed:
        best_cost = sum(Tour.Dis.values())
        best_insertion = []
        for tour in tours:
            if tour.demand + Data["Clusters"][node].demand <= Data["C"]:
                for pos in range(len(tour) - 1):
                    cost_change = tour.insertion_cost(node, pos)
                    if cost_change < best_cost:
                        best_insertion = [tour, pos]
                        best_cost = cost_change

        if best_insertion:
            best_insertion[0].insert(node, best_insertion[1])
        else:
            unable_2_route.append(node)

            tours, unable_2_route = create_new_route(M, tours, unable_2_route)

    return tours, unable_2_route


def create_new_route(M, tours, unable_2_route):
    if unable_2_route:
        if M:
            if len(tours) < M:
                node = rn.choice(unable_2_route)
                new_tour = Tour(["D0", node, "D0"])
                new_tour.calc_demand()
                new_tour.calc_cost()
                tours.append(new_tour)
                unable_2_route.remove(node)
        else:
            node = rn.choice(unable_2_route)
            new_tour = Tour(["D0", node, "D0"])
            new_tour.calc_demand()
            new_tour.calc_cost()
            tours.append(new_tour)
            unable_2_route.remove(node)

    return tours, unable_2_route


def update_regret_values(insertion_cost, regret_value, toInsert, tour):
    # update the insertion cost and regret value for unrouted
    # Run this after inserting the node
    node, move = toInsert
    move = move["position"]
    del regret_value[node]
    del insertion_cost[node]
    unable_2_route = []
    un_routed = list(regret_value.keys())
    for n in un_routed:
        if tour.demand + Tour.Data["Clusters"][n].demand <= Tour.Data["C"]:
            for pos in range(move[1], len(tour)-1):
                insertion_cost[n][(move[0], pos)] = tour.insertion_cost(n, pos)
        else:
            for pos in range(len(tour)-2):
                if (move[0], pos) in insertion_cost[n].keys():
                    del insertion_cost[n][(move[0], pos)]

        sorted_insertion_cost = sorted(insertion_cost[n].items(), key=lambda x: x[1])

        if len(sorted_insertion_cost) == 1:
            regret_value[n] = {"value": sorted_insertion_cost[0][1],
                                  "position": sorted_insertion_cost[0][0]}
        elif len(sorted_insertion_cost) == 0:
            unable_2_route.append(n)
            del regret_value[n]
        else:
            regret_value[n] = {"value": sorted_insertion_cost[1][1] - sorted_insertion_cost[0][1],
                                  "position": sorted_insertion_cost[0][0]}

    return insertion_cost, regret_value, unable_2_route


def Regret_insertion(Data, tours, un_routed):
    #  calculate a regret value equal to the difference in cost between two solutions in which i is inserted in its best
    #  route or in its second best route. The customer i with the maximum regret value is chosen to be inserted.
    # Worst time complexity O(N**3)
    M = Tour.Data["Vehicles"]
    unable_2_route = []
    regret_value = {}
    insertion_cost = {}
    # initiation
    for node in un_routed:
        insertion_cost[node] = {}
        for inx, tour in enumerate(tours):
            if tour.demand + Data["Clusters"][node].demand <= Data["C"]:
                for pos in range(len(tour) - 1):
                    insertion_cost[node].update({(inx, pos): tour.insertion_cost(node, pos)})

        sorted_insertion_cost = sorted(insertion_cost[node].items(), key=lambda x: x[1])

        if len(sorted_insertion_cost) == 0:
            unable_2_route.append(node)
        elif len(sorted_insertion_cost) == 1:
            regret_value[node] = {"value": sorted_insertion_cost[0][1],
                                  "position": sorted_insertion_cost[0][0]}
        else:
            regret_value[node] = {"value": sorted_insertion_cost[1][1]-sorted_insertion_cost[0][1],
                                  "position": sorted_insertion_cost[0][0]}
    # main body of the algorithm
    while regret_value:
        toInsert = max(regret_value.items(), key=lambda x: x[1]["value"])
        tour = tours[toInsert[1]["position"][0]]
        # update the regret_value
        tour.insert(toInsert[0], toInsert[1]["position"][1])
        un_routed.remove(toInsert[0])
        insertion_cost, regret_value, unable_2_route_new = update_regret_values(insertion_cost, regret_value, toInsert, tour)
        unable_2_route = list(set(unable_2_route) | set(unable_2_route_new))
        tours, unable_2_route = create_new_route(M, tours, unable_2_route)

    return tours, unable_2_route


def destroy(tours, unable_2_route, M=None):

    un_routed = unable_2_route[:]
    N_remove = math.ceil(0.3 * len(Tour.Data["Clusters"])) - len(un_routed)

    rand_number = rn.random()
    if rand_number < 0.6:
        destroyed_tours, un_routed = Shaw_removal(tours, un_routed, N_remove)

    elif rand_number < 0.9:
        destroyed_tours, un_routed = Worst_removal(tours, un_routed, N_remove)

    elif rand_number < 1:
        destroyed_tours, un_routed = Random_removal(tours, un_routed, N_remove)

    inx = len(destroyed_tours) - 1

    while inx >= 0:
        if len(destroyed_tours[inx]) <= 2:
            del destroyed_tours[inx]
        inx -= 1

    if len(destroyed_tours) > M:
        destroyed_tours, un_routed = Route_removal(destroyed_tours, un_routed, M)

    return destroyed_tours, un_routed


def repair(Data, tours, un_routed):
    M = Data["Vehicles"]
    while len(tours) < M and un_routed:
        tours, un_routed = create_new_route(M, tours, un_routed)


    rand = rn.random()
    if rand < 0.6:
        tours, un_routed = Greedy_insertion(Data, tours, un_routed)

    else:
        tours, un_routed = Regret_insertion(Data, tours, un_routed)

    return tours, un_routed


def feasibility_check(Data, tours, un_routed=[]):
    all_nodes = []
    condition = True
    for tour in tours:
        all_nodes += tour.without_depot()
        condition = condition and tour.demand <= Data["C"]
    if not condition:
        print("Vehicle capacity is not meet")
    if Data["Vehicles"] != 0:
        # print(len(tours))
        pass
        # condition = condition and Data["Vehicles"] == len(tours)
    if not condition:
        print("The number of vehicle is not meet")
    condition = len(all_nodes) + len(un_routed) == len(Data["Clusters"]) and condition
    if not condition:
        print("Not all the customer visited")
        print(set(list(Data["Clusters"].keys())) - set(all_nodes))
    return condition


def accept(M, tours, un_routed, best_value, temperature):
    flag = False
    current_cost = sum([t.cost for t in tours]) + 10000 * (len(un_routed) + abs(len(tours) - M))
    if current_cost < best_value:
        flag = True
    elif rn.random() <= math.exp(-1 * (current_cost - best_value)/temperature):
        flag = True

    return flag


def LNS(Data, Dis):
    M = Data["Vehicles"]
    # initial tours
    Tour.Data = Data
    Dis["D0", "D0"] = 0
    Tour.Dis = Dis
    V_c = list(Data["Clusters"].keys())
    current_tours = Savings_Alg(Data, Dis, V_c)
    pickle_tours = pickle.dumps(current_tours)
    current_unrouted = []
    un_routed = []
    # LNS parameters
    max_iter = 50000
    max_time = 300 # sec
    max_no_improve = 5000

    start_temp = sum([t.cost for t in current_tours])
    current_temp = start_temp
    cooling_rate = 0.9975

    start = time.time()
    counter = 0
    no_improve = 0
    best_value = sum(Dis.values())
    best_tour = [copy.deepcopy(t) for t in current_tours[:]]

    while counter < max_iter and no_improve < max_no_improve and time.time() < start + max_time:
        # print(f"The current route{current_tours}")
        current_tours = pickle.loads(pickle_tours)
        destroyed_tours, un_routed = destroy(current_tours, current_unrouted, Data["Vehicles"])
        new_tours, un_routed = repair(Data, destroyed_tours, un_routed)
        # print(un_routed)

        counter += 1
        if accept(M, new_tours, un_routed, best_value, current_temp):
            pickle_tours = pickle.dumps(new_tours)
            current_unrouted = un_routed[:]
            #print("Current is changed")
            current_value = sum([t.cost for t in new_tours])
            if round(current_value,4) < round(best_value,4):
                best_tour = pickle.dumps(new_tours)
                best_value = current_value + 10000 * (len(un_routed) + abs(len(new_tours) - M))
                print(f"New_best: {best_value}")
                no_improve = 0
            else:
                no_improve += 1
        else:
            no_improve += 1

        current_temp = current_temp * cooling_rate

    best_tour = pickle.loads(best_tour)
    return best_value, best_tour


def read_data(Path_2_file, M):
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


    #clean_data["X_range"] = x_range
    #clean_data["Y_range"] = y_range

def dist_matrix_calc(Data):
    dist_matrix = {}

    for cus1, cus2 in it.combinations(Data["Clusters"].values(), 2):
        dist_matrix[cus1.ID, cus2.ID] = math.sqrt((cus1.coord[0]-cus2.coord[0])**2 + (cus1.coord[1]-cus2.coord[1])**2)
        dist_matrix[cus2.ID, cus1.ID] = dist_matrix[cus1.ID, cus2.ID]

    depot = Data["depot"]
    for cus in Data["Clusters"].values():
        dist_matrix["D0", cus.ID] = math.sqrt((depot.coord[0]-cus.coord[0])**2 + (depot.coord[1]-cus.coord[1])**2)
        dist_matrix[cus.ID, "D0"] = dist_matrix["D0", cus.ID]

    return dist_matrix


def run_LNS(file_name=None, M=0):
    start = time.time()
    if not file_name:
        file_name = "P/P-n45-k5.vrp"
    Path_2_file = os.getcwd().replace("projection", "data") + "/" + file_name
    data = read_data(Path_2_file, M)
    dis = dist_matrix_calc(data)

    best_value, best_tour = LNS(data, dis)

    print(f"Is the final solution feasible ? {feasibility_check(data, best_tour)}")

    for tour in best_tour:
        print(tour)
    runtime = round(time.time() - start,2)
    print(runtime)
    return round(best_value,2), len(best_tour), runtime

import glob
import pandas as pd
if __name__ == "__main__":
    file_names = glob.glob("data/P/*.vrp")
    results = []
    for file in ["data/P/P-n50-k10.vrp"]: # file_names:
        M = int(file.split("k")[1].split(".vrp")[0])
        results.append([file.replace("data/P/",""), *run_LNS(file, M)])

    df1 = pd.DataFrame(results,
                       columns=['Instance', 'Obj', 'Vehicles', 'Time'])
    df1.to_csv("results.csv")
