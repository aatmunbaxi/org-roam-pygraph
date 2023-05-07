#!/usr/bin/python

import os , glob
import warnings

import numpy as np

from orgparse import load as orgload

from lib.RoamNode import RoamNode as Node

from scipy.sparse.csgraph import shortest_path

class RoamGraph():
    """
    Stores information of a (possibly filtered) roam directory.

    Attributes
    -----------
    dirname : str
        name of directory to search
    tags : str list
        list of tags to exclude
    """
    def __init__(self, dirname, tags = None , exclude = False ,recurse = False):
        super(RoamGraph, self).__init__()

        self.dirname = dirname
        self.filter_tags= tags
        self.exclude = exclude

        if recurse:
            filepaths = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "**/*.org", recursive=recurse)]
        else:
            filepaths = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "*.org")]

        self.nodes = [ Node(path) for path in filepaths ]

        self.__cleanup_node_data()

        if self.filter_tags:
            self.__filter_tags()


    def __filter_tags(self):
        bool_tags_list = [self.nodes[i].has_tags(self.filter_tags) for i in range(len(self.nodes))]
        if self.exclude:
            bool_tags_list = [not i for i in bool_tags_list]

        self.nodes = [i for (i,v) in zip(self.nodes, bool_tags_list) if v]

    def adjacency_matrix(self, directed = False, transpose = False):
        """
        Builds adjacency matrix of org-roam notes.

        directed -- whether to consider the zettel graph as directed (default False)
        """
        N = len(self.nodes)

        graph = np.zeros((N,N))

        if directed:
            for i in range(N):
                for j in range(N):
                    if i != j:
                        graph[i,j] = self.__adjacency_entry(i,j,directed = True)
            if transpose:
                return graph.transpose()

            return graph

        for i in range(N):
            for j in range(i+1 , N):
                graph[i,j] = self.__adjacency_entry(i,j, directed = False)
                graph[j,i] = graph[i,j]

        return graph

    def distance_matrix(self, directed = False, transpose= False):
        """
        Computes distance matrix of graph

        directed -- Consider graph as directed (default False)
        """
        return shortest_path(self.adjacency_matrix(directed=directed) , directed=directed)

    def get_fnames(self):
        """
        Get filenames of graph
        """
        return [node.fname for node in self.nodes]

    def get_nodes(self):
        return self.nodes

    def get_IDs(self):
        """
        Gets org-roam IDs of graph
        """
        return [node.id for node in self.nodes]

    # def contains_tag(self,idx):
    #     """
    #     Determines if node at index idx contains any exclude filter_tags
    #     """
    #     body = self.nodes[i].body(fmt='raw')
    #     return any(tag in body for tag in self.filter_tags)

    def __adjacency_entry(self, i,j, directed = False):
        if self.nodes[i].id in self.nodes[j].body():
            return 1

        if not directed:
            if self.nodes[j].id in self.nodes[i].body():
                return 1

        return np.inf

    def __cleanup_node_data(self):
        nones = []
        for node in self.nodes:
            if node.fob is None:
                warnings.warn(f"{os.path.basename(node.fname)} has no ID property. Removing from graph.")
                nones.append(i)

        self.nodes = [i for i in self.nodes if i not in nones]
