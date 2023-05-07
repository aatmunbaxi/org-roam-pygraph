#!/usr/bin/env python3

from lib.RoamGraph import RoamGraph

# VR persistence for undirected graphs
from gtda.homology import VietorisRipsPersistence

# FP persistence for directed graphs
from gtda.homology import FlagserPersistence

# ######################################
# Roam notes directory (need trailing /)
ROAM_DIR = ""

# List of tags to filter by
tags = [ ]

# Initialize RoamGraph object
# Choose to include or exclude tags
network = RoamGraph(ROAM_DIR, tags , exclude = False)

# Compute distance matrix of undirected network
graph = network.distance_matrix(directed = False)

# or directed
# graph = network.distance_matrix(directed = False)

# For undirected persistnce
VR = VietorisRipsPersistence(metric='precomputed')

# For directed persistence
# FP = FlagserPersistence()

# Persistence diagrams for undirected
diagrams = VR.fit_transform(graph)

# Directed graph persistence
# diagrams = FP.fit_transform(graph)

# Open persistence diagram in browser
plot_diagram(diagrams[0]).show()
