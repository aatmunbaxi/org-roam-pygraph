#!/usr/bin/python

import os , glob , re
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
    recurse : bool
        recurse into dirname
    ex_tags : str list
        list of tags to filter by. Regex supported
    include_ex : bool
        whether to exclude tags or include
    ex_tags : compiled python regex list
        list of regexes to filter tags by
    include_rx : bool
        include regex matched nodes
    nodes : list RoamNode
        list of RoamNodes
    """
    def __init__(self, dirname,
               recurse = False,
               tags_exact = None ,
               include_exact = True ,
               tags_rx = [],
               include_rx = True,
               ):
        """
        Constructor for RoamGraph

        Params
        dirname -- directory to search for .org files
        recurse (opt) -- whether to recurse in directory of not
        tags_exact (opt) -- list of str to match roam tags exactly
        include_exact (opt) -- bool. Include exact matched tags in graph
        tags_rx (opt) -- list of compiled python regexes to match in roam tags
        include_rx (opt) -- bool. Include regex matched tags in graph
        """

        super(RoamGraph, self).__init__()

        self.dirname = dirname

        self.ex_tags = tags_exact
        self.rx_tags= tags_rx

        self.include_ex = include_exact
        self.include_rx = include_rx

        if recurse:
            filepaths = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "**/*.org", recursive=recurse)]
        else:
            filepaths = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "*.org")]

        self.nodes = [ Node(path) for path in filepaths ]

        self.__cleanup_node_data()

        if self.ex_tags:
            self.__filter_ex_tags()

        if self.rx_tags:
            self.__filter_rx_tags()

    def __filter_ex_tags(self):
        """
        Filters exact tags from node list
        """
        bool_tags_list = [self.nodes[i].has_exact_tags(self.ex_tags) for i in range(len(self.nodes))]
        if not self.include_ex:
            bool_tags_list = [not i for i in bool_tags_list]

        self.nodes = [i for (i,v) in zip(self.nodes, bool_tags_list) if v]

    def __filter_rx_tags(self):
        """
        Filters exact tags from node list
        """
        bool_tags_list = [self.nodes[i].has_rx_tags(self.rx_tags) for i in range(len(self.nodes))]
        if not self.include_rx:
            bool_tags_list = [not i for i in bool_tags_list]

        self.nodes = [i for (i,v) in zip(self.nodes, bool_tags_list) if v]

    def adjacency_matrix(self, directed = False, transpose = False):
        """
        Builds adjacency matrix of graph nodes

        directed -- whether to consider the zettel graph as directed (default False)
        transpose -- reverse direction of graph paths (default False)

        Returns graphs adjacency matrix
        """
        N = len(self.nodes)

        graph = np.zeros((N,N))

        if directed:
            for i in range(1,N):
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
        transpose -- reverse direction of graph paths (default False)

        Returns graphs distance matrix
        """
        return shortest_path(self.adjacency_matrix(directed=directed) , directed=directed)

    def get_fnames(self):
        """
        Get filenames of graph
        """
        return [node.fname for node in self.nodes]

    def get_nodes(self):
        """
        Returns list of nodes
        """
        return self.nodes

    def get_IDs(self):
        """
        Returns list of node IDs
        """
        return [node.id for node in self.nodes]

    def get_names(self):
        return [node.name for node in self.nodes]


    def __adjacency_entry(self, i,j, directed = False):
        """
        Determines if two nodes are adjacent
        """
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
                warnings.warn(f"{os.path.basename(node.fname)} has bad orgparse. Removed from graph.")
                nones.append(node)
            if node.id is None:
                warnings.warn(f"{os.path.basename(node.fname)} has malformed or no ID property. Removed from graph.")
                nones.append(node)

        self.nodes = [i for i in self.nodes if i not in nones]
