import time
import random as rn
import sys
import copy
from collections import deque


class Tour:
    Data = None

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

    def calc_demand(self):
        self.demand = sum(Tour.Data["Clusters"][clu].demand for clu in self[1:-1])

    def calc_cost(self, Dis):
        cost = 0
        current = self.seq[0]
        for next in self.seq[1:]:
            cost += Dis[current, next]
            if next != "D0":
                cost += Tour.Data["Clusters"][next].service_time
            current = next
        self.cost = cost

    def insertion_cost(self, Dis, node, pos):
        cost_change = Dis[self[pos],node] + Dis[node,self[pos+1]] - Dis[self[pos],self[pos+1]] \
                      + Tour.Data["Clusters"][node].service_time
        return cost_change

    def insert(self,Dis, node, pos):
        self.cost += self.insertion_cost(Dis, node, pos)
        self.seq.insert(pos+1,node)
        self.demand += Tour.Data["Clusters"][node].demand

    def remove(self, Dis, node):
        inx = self.seq.index(node)
        if inx != 0 or inx != len(self)-1:
            if len(self) > 3:
                self.cost += -Dis[self[inx-1], self[inx]] - Dis[self[inx], self[inx+1]] + Dis[self[inx-1], self[inx+1]] \
                             - Tour.Data["Clusters"][node].service_time
            else:
                self.cost = 0
            self.demand -= Tour.Data["Clusters"][node].demand
        else:
            sys.exit("Try to remove the depot from tour")
        self.seq.remove(node)

    def without_depot(self):
        temp_seq = copy.copy(self.seq)
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
        tour_obj.calc_cost(Dis)
        tours.append(tour_obj)
        emerging_route_nodes = None

    return tours


def destroy(Dis, destroyed_tours):
    un_routed = []
    # remove some persentage of the nodes in tours
    for inx in range(len(destroyed_tours)):
        new_tour = copy.copy(destroyed_tours[inx])
        for visit in destroyed_tours[inx][1:-1]:
            if rn.random() <= 0.2:
                un_routed.append(visit)
                new_tour.remove(Dis, visit)
        destroyed_tours[inx] = new_tour

    # delete the whole tour
    inx = len(destroyed_tours) -1
    while inx >= 0:
        if len(destroyed_tours[inx]) < 3:
            del destroyed_tours[inx]
            inx -= 1
            continue
        if rn.random() < 0.15:
            un_routed += destroyed_tours[inx].without_depot()
            del destroyed_tours[inx]
        inx -= 1

    return destroyed_tours, un_routed


def insertion(Data, Dis, tours, node):
    best_cost = sum(Dis.values())
    best_insertion = []
    for tour in tours:
        if tour.demand + Data["Clusters"][node].demand <= Data["C"]:
            for pos in range(len(tour)-1):
                cost_change = tour.insertion_cost(Dis, node, pos)
                if cost_change < best_cost:
                    best_insertion = [tour, pos]
                    best_cost = cost_change

    if best_insertion:
        best_insertion[0].insert(Dis,node, best_insertion[1])
    else:
        new_tour = Tour(["D0", node, "D0"])
        new_tour.calc_demand()
        new_tour.calc_cost(Dis)
        tours.append(new_tour)
    return tours


def repair(Data, Dis, tours, un_routed):
    for node in un_routed:
        tours = insertion(Data, Dis, tours, node)
    un_routed = []
    return tours


def accept(Data, tours):
    Total_N_nodes = 0
    condition = True
    for tour in tours:
        Total_N_nodes += len(tour.without_depot())
        condition = condition and tour.demand <= Data["C"]

    return Total_N_nodes == len(Data["Clusters"]) and condition


def LNS(Data, Dis):
    max_iter = 10000
    max_time = 300 # sec
    max_no_improve = 6000

    Tour.Data = Data

    V_c = list(Data["Clusters"].keys())
    tours = Savings_Alg(Data, Dis, V_c)

    start = time.time()
    counter = 0
    no_improve = 0
    best_value = sum([t.cost for t in tours])
    best_tour = [t.seq[:] for t in tours]
    while counter < max_iter and no_improve < max_no_improve and time.time() < start + max_time:
        destroyed_tours, un_routed = destroy(Dis, tours)
        tours = repair(Data, Dis, destroyed_tours, un_routed)
        counter += 1
        if not accept(Data, tours):
            print("Big problem")
        if sum([t.cost for t in tours]) < best_value:
            best_value = sum([t.cost for t in tours])
            best_tour = [t.seq[:] for t in tours]
            print(best_value)
            no_improve = 0
        else:
            no_improve += 1

    return best_value, best_tour

