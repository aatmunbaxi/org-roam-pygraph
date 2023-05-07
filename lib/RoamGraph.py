#!/usr/bin/python

import os , glob
import warnings

import numpy as np

from orgparse import load as orgload

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
        self.tags= tags
        self.exclude = exclude

        if recurse:
            filenames = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "**/*.org", recursive=recurse)]
        else:
            filenames = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "*.org")]


        # filenames = [os.path.join(dirname ,f) for f in glob.glob(dirname  + "*.org")]
        fileobs = [orgload(fname) for fname in filenames]
        roamIDs = [ f.get_property('ID') for f in fileobs ]

        self.nodedata = [(a,b,c) for (a,b,c) in zip(filenames, fileobs, roamIDs)]

        self.__cleanup_node_data()

        if self.tags:
            self.__filter_tags()


    def __filter_tags(self):
        bool_tags_list = [self.contains_tag(i) for i in range(len(self.nodedata))]
        if self.exclude:
            bool_tags_list = [not i for i in bool_tags_list]

        self.nodedata = [i for (i,v) in zip(self.nodedata, bool_tags_list) if v]


    def adjacency_matrix(self, directed = False, transpose = False):
        """
        Builds adjacency matrix of org-roam notes.

        directed -- whether to consider the zettel graph as directed (default False)
        """
        N = len(self.nodedata)

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
        return [node[1] for node in self.nodedata]

    def get_nodedata(self):
        return self.nodedata

    def get_IDs(self):
        """
        Gets org-roam IDs of graph
        """
        return [node[2] for node in self.nodedata]

    def contains_tag(self,idx):
        """
        Determines if node at index idx contains any exclude tags
        """
        body = self.nodedata[idx][1].root.get_body(format='raw')
        return any(tag in body for tag in self.tags)

    def __adjacency_entry(self, i,j, directed = False):
        for subheading in self.nodedata[i][1].root:
            if self.nodedata[j][2] in subheading.get_body(format='raw'):
                return 1

        if not directed:
            for subheading in self.nodedata[j][1].root:
                if self.nodedata[i][2] in subheading.get_body(format='raw'):
                    return 1

        return np.inf

    def __cleanup_node_data(self):
        nones = []
        for i in self.nodedata:
            if i[2] is None:
                warnings.warn(f"{os.path.basename(i[0])} has no ID property. Removing from graph.")
                nones.append(i)

        self.nodedata = [i for i in self.nodedata if i not in nones]
