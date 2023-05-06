#!/usr/bin/env python3

import os , glob
import numpy as np
from orgparse import load as orgload

from scipy.sparse.csgraph import floyd_warshall
from ripser import ripser
from persim import plot_diagrams

org_roam_dir = "/home/aatmun/Documents/org/roam/"
roam_fnames = [os.path.join(org_roam_dir, f) for f in glob.glob( org_roam_dir + "*.org" )]


file_obs = [orgload(fname) for fname in roam_fnames]
# print(file_obs[3].root[0])
roam_IDs = [ fname.get_property('ID') for fname in file_obs ]

ID_object = { k:v for (k,v) in zip(roam_IDs, file_obs) }
# print(ID_object)

# print(roam_IDs)


def is_adjacent(ID1, ID2, ID_dict):

    for subheading in ID_dict[ID1].root:
        # print(subheading.get_body(format='raw'))
        if ID2 in subheading.get_body(format='raw'):
            return 1

    for subheading in ID_dict[ID2].root:
        # print(subheading.get_body(format='raw'))
        if ID1 in subheading.get_body(format='raw'):
            return 1

    return np.inf

# print(roam_IDs[0])
# print(roam_IDs[5])
# print(is_adjacent(roam_IDs[0] , roam_IDs[5], ID_object))

adj_mat = np.zeros((len(roam_IDs), len(roam_IDs)))


for i in range(0,len(adj_mat)):
   for j in range(i+1, len(adj_mat)):
       adj_mat[i,j] = is_adjacent(roam_IDs[i], roam_IDs[j], ID_object)
       adj_mat[j,i] = adj_mat[i,j]




def is_diag(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            if matrix[i,j] != matrix[j,i]:
                return False


    return True

# type(convert_adj_dis(adj_mat))
# adj_mat.shape
# print(is_diag(convert_adj_dis(adj_mat)))


# distance_mat = convert_adj_dis(adj_mat)
distance_mat = floyd_warshall(adj_mat)


dgms = ripser( distance_mat , distance_matrix = True )['dgms']
plot_diagrams(dgms,show= True)
