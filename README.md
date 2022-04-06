# Capacited Vehicle Routing Problem (CVRP) Simple, Fast and flexible solver

The solver has three simple steps
-  Aggregation of customers based on given subgroups (zones, clusters, or micro postcodes) and creating the reduced graph.
-  Solving a CVRP on the reduced graph with Large Neighborhood Search (LNS).
-  Disaggregating the clusters sequence to customer nodes sequence.

