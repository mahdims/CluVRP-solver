from gurobipy import Model, quicksum, GRB
from concorde.tsp import TSPSolver
import numpy as np
import itertools as it
import sys


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


def subtourelim(model, where):
    # Callback - use lazy constraints to eliminate sub-tours
    if where == GRB.callback.MIPSOL:
        selected = []
        sol = {}
        # make a list of edges selected in the solution
        for i in Gnodes:
            for j in Gnodes:
                if j != i:
                    sol[i, j] = model.cbGetSolution(model._vars[i, j])
                    if sol[i, j] > 0.5:
                        selected.append((i, j))
        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        if len(tour) < N:
            # add a subtour elimination constraint
            expr = 0
            for i in range(len(tour)):
                for j in range(len(tour)):
                    if j != i:
                        expr += model._vars[tour[i], tour[j]]
                model.cbLazy(expr <= len(tour) - 1)


def subtour(edges):
    # Given a list of edges, finds the shortest subtour
    visited = {}
    selected = {}
    for i in Gnodes:
        visited[i] = False
        selected[i] = []
    cycles = []
    lengths = []

    for x, y in edges:
        selected[x].append(y)

    while True:
        current = list(visited.keys())[list(visited.values()).index(False)]
        thiscycle = [current]

        while True:
            visited[current] = True
            neighbors = [x for x in selected[current] if not visited[x]]
            if len(neighbors) == 0:
                break
            current = neighbors[0]
            thiscycle.append(current)
        cycles.append(thiscycle)
        lengths.append(len(thiscycle))

        if sum(lengths) == N:
            break

    return cycles[lengths.index(min(lengths))]


def TSP_model(e_ttime, Nodes, start=None, end=None):
    global Gnodes, N
    Gnodes = list(Nodes.keys())
    N = len(Gnodes)
    # route that do not need a tsp to be solved
    if end:
        Big_m = e_ttime.values.max()
        e_ttime[start][end] = e_ttime[end][start] = -1 * Big_m

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
        if N <= 2:
            return Gnodes, sum(sum(e_ttime.values))

    TSP = Model("Tsp")

    # Create variables

    x = {}
    for i, j in it.product(Gnodes, Gnodes):
        x[i, j] = TSP.addVar(obj=e_ttime[i][j], vtype=GRB.BINARY, name='e' + str(i) + '_' + str(j))

    TSP._vars = x
    TSP.update()
    # Add flow balance constraints
    TSP.addConstrs(quicksum(x[i, j] for i in Gnodes if j != i) == 1 for j in Gnodes)
    TSP.addConstrs(quicksum(x[i, j] for j in Gnodes if j != i) == 1 for i in Gnodes)

    TSP.update()
    # Optimize model
    TSP.Params.OutputFlag = 0
    TSP.params.LazyConstraints = 1
    TSP.optimize(subtourelim)
    if TSP.status != 2:
        print("TSP is not feasible")
        return Gnodes
    solution = TSP.getAttr('x', x)
    selected = [(i, j) for i, j in x.keys() if solution[i, j] > 0.5]
    route = subtour(selected)
    if len(route) != N:
        sys.exit(Gnodes)

    objval = TSP.Objval
    if end:
        # we are in dis aggregation that solves TSP to find hamiltonian paths
        route = Route_correction(route, start, end)
        objval += Big_m

    return route, objval


# Solve with concorde
def TSP_concorde(e_ttime, Gnodes):

    solver = TSPSolver.from_matrix(e_ttime.values)
    tour_data = solver.solve(time_bound=5, silent=10)

    if not tour_data.success:
        print("Concorde failed")
        route, objval = "Fail", "Fail"
        return (route, objval)
    route = []
    for i in tour_data.tour:
        route.append(Gnodes[i])

    return route, tour_data.optimal_value

