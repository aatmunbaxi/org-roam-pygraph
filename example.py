#!/usr/bin/env python3

from lib.RoamGraph import RoamGraph

# ######################################
# Roam database path (~ expansion allowed)
ROAM_DB = ""

# List of tags to filter by
tags = [ ]

# Initialize RoamGraph object
# Choose to include or exclude tags
network = RoamGraph(ROAM_DIR)

# Filter tags
filtered_network = network.filter_tags(tags, exclude = False)

# Compute distance matrix of undirected network
graph = network.distance_matrix(directed = False)

# Directed filtered distance matrix
filtered_graph = filtered_network.distance_matrix(directed = True)
