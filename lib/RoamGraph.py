#!/usr/bin/python
import os, glob, re
import warnings
import sqlite3 as sql
import copy
import numpy as np
import pandas as pd

from lib.RoamNode import RoamNode as Node

from scipy.sparse.csgraph import shortest_path


class RoamGraph:
    """
    Stores information of a (possibly filtered) roam directory.

    Attributes
    -----------
    db : str
        path to org-roam-db
    nodes : list RoamNode
        list of RoamNodes
    """

    def __init__(self, db):
        """
        Constructor for RoamGraph

        Params
        db -- path to org-roam db (required)
        """

        super(RoamGraph, self).__init__()

        self.db_path = os.path.expanduser(db)

        fnames = self.__init_fnames(self.db_path)
        titles = self.__init_titles(self.db_path)
        ids = self.__init_ids(self.db_path)
        tags = self.__init_tags(self.db_path)
        links_to = self.__init_links_to(self.db_path)

        self.nodes = [
            Node(a, b, c, d, e)
            for (a, b, c, d, e) in zip(fnames, titles, ids, tags, links_to)
        ]

    def get_nodes(self):
        """
        Returns list of nodes
        """
        return self.nodes

    def filter_tags(self, tags=None, exclude=True, regex=False):
        """
        Extract subgraph based on filtering of tags

        Params
        tags -- list (str) (default None)
             list of tags to filter
        exclude -- bool (default True)
                exclude tags if True (default True)
        regex -- bool (default False)
                interpret tags param as list of regexes.

        Returns filtered subgraph as copy
        """
        if not tags:
            raise ValueError("taglist must be nonempty")

        subgraph = copy.deepcopy(self)
        if not regex:
            subgraph.__filter_tags(tags, exclude)
            return subgraph

        if regex:
            subgraph.__filter_rx_tags(tags, exclude)
            return subgraph

    def __filter_tags(self, tags, exclude):
        """
        Filters tags by exact match

        tags -- list (str)
             Tags to match
        exclude -- bool
             To exclude or no
        """
        scope = range(len(self.nodes))
        tfilter = [node.has_tag(tags) for node in self.nodes]
        if exclude:
            tfilter = [not b for b in tfilter]
        self.nodes = [node for (node, b) in zip(self.nodes, tfilter) if b]

    def __filter_rx_tags(self, tags, exclude):
        """
        Filters tags by regex

        Params
        tags -- list regexp
             Regexes to compiler by
        exclue -- bool
             To exclude tags or not

        Returns filtered subgraph as copy
        """
        tags = set(map(re.compile, tags))

        scope = range(len(self.nodes))
        tfilter = [node.has_regex_tag(tags) for node in self.nodes]
        if exclude:
            tfilter = [not b for b in tfilter]
        self.nodes = [node for (node, b) in zip(self.nodes, tfilter) if b]

    def __init_ids(self, dbpath):
        """
        Initializes list of IDs for each node

        Params
        dbpath -- str
              database path

        Returns list of roam-node ids
        """
        id_query = "SELECT id FROM nodes ORDER BY id ASC;"
        try:
            with sql.connect(dbpath, uri=True) as con:
                csr = con.cursor()
                query = csr.execute(id_query)
                return [i[0].replace('"', "") for i in query.fetchall()]

        except sql.Error as e:
            print("Connection failed: ", e)

    def __init_fnames(self, dbpath):
        """
        Initializes list of filenames for each node

        Params
        dbpath -- str
               database path


        Returns list of roam-node filepaths
        """
        fname_query = "SELECT file FROM nodes ORDER BY id ASC;"
        try:
            with sql.connect(dbpath, uri=True) as con:
                csr = con.cursor()
                query = csr.execute(fname_query)
                return [i[0].replace('"', "") for i in query.fetchall()]

        except sql.Error as e:
            print("Connection failed: ", e)

    def __init_titles(self, dbpath):
        """
        Initializes list of titles for each node

        Params
        dbpath -- str
               database path


        Returns list of roam-node titles
        """
        title_query = "SELECT title FROM nodes ORDER BY id ASC;"
        try:
            with sql.connect(dbpath, uri=True) as con:
                csr = con.cursor()
                query = csr.execute(title_query)
                return [i[0].replace('"', "") for i in query.fetchall()]

        except sql.Error as e:
            print("Connection failed: ", e)

    def __init_tags(self, dbpath):
        """
        Initializes list of tags for each node

        Params
        dbpath -- str
                database path

        Returns list of roam-node taglists (as a set)
        """
        tags_query = ("SELECT nodes.id, GROUP_CONCAT(tags.tag) AS tags FROM nodes LEFT JOIN tags ON nodes.id = tags.node_id GROUP BY nodes.id ORDER BY nodes.id ASC;")
        try:
            with sql.connect(dbpath, uri=True) as con:
                csr = con.cursor()
                query = csr.execute(tags_query)
                clean = lambda s: s.replace('"', "")
                return [set(map(clean, i[0].split(","))) for i in query.fetchall()]

        except sql.Error as e:
            print("Connection failed: ", e)

    def __init_links_to(self, dbpath):
        """
        Initializes list of links

        Params
        dbpath -- str
               database path


        Returns list of roam-node links
        """
        links_to_query = "SELECT n.id, GROUP_CONCAT(l.dest) FROM nodes n LEFT JOIN links l ON n.id = l.source GROUP BY n.id ORDER BY n.id ;"
        try:
            with sql.connect(dbpath, uri=True) as con:
                csr = con.cursor()
                query = csr.execute(links_to_query)
                clean = lambda s: s.replace('"', "")
                links = query.fetchall()

                return [set(map(clean, i[1].split(","))) if i[1] else {} for i in links]

        except sql.Error as e:
            print("Connection failed: ", e)

    def remove_orphans(self):
        """
        Removes orphan nodes

        Returns orphanless RoamGraph (not done in-place)
        """
        orphanless = copy.copy(self)
        not_orphan = lambda node: not self.__is_orphan(node)

        orphanless.nodes = list(filter(not_orphan, self.nodes))

        return orphanless

    def adjacency_matrix(self, directed=False, reverse=False):
        """
        Builds adjacency matrix of graph nodes
        Two nodes i and j and adjacent if the i,jth entry of the
        adjacency matrix is 1, and np.inf if they are not adjacent.

        directed -- bool
                whether to consider the zettel graph as directed (default False)
        reverse -- bool
                reverse direction of graph paths (default False)
                By default, node1 points to node2 if the ID of node2 is linked
                in the body text of node1

        Returns graph's adjacency matrix
        """
        N = len(self.nodes)

        graph = np.full((N, N),np.inf)

        if directed:
            for i in range(N):
                for j in [k for k in range(N) if k != i]:
                    if self.nodes[i].links(self.nodes[j], directed=True):
                        graph[i, j] = 1

            if reverse:
                return np.transpose(graph)

            return graph

        for i in range(N):
            for j in range(i + 1, N):
                if self.nodes[i].links(self.nodes[j]):
                    graph[i, j] = graph[j, i] = 1

        return graph

    def adjacency_df(self, directed=False, reverse=False):
        """
        Builds adjacency dataframe of graph nodes
        Two nodes i and j and adjacent if the i,jth entry of the
        adjacency matrix is 1, and np.inf if they are not adjacent.
        Rows and columns are labelled by the title of the node

        directed -- bool
                whether to consider the zettel graph as directed (default False)
        reverse -- bool
                reverse direction of graph paths (default False)
                By default, node1 connects to node2 if the ID of node2 is linked
                in the body text of node1

        Returns graph's adjacency matrix
        """
        names = [node.title for node in self.nodes]
        N = len(self.nodes)

        df = pd.DataFrame(np.inf, dtype=np.float32, columns=names, index=names)

        if directed:
            for i in range(N):
                for j in [k for k in range(N) if k != i]:
                    if self.nodes[i].links(self.nodes[j], directed=True):
                        df.values[i, j] = 1

            if reverse:
                return pd.DataFrame(df.values.T, columns=names, index=names)

            return df

        for i in range(N):
            for j in range(i + 1, N):
                if self.nodes[i].links(self.nodes[j]):
                    df.values[i, j] = df.values[j, i] = 1

        return df

    def adjacency_list(identifier = "title", directed = False):
        """
        Creates edge list of graph.
        More space efficient for non-sparse graphs

        identifier -- identifier for each node to use in edge list
                      options are "title", "filename", and "ID"
        """
        try:
            if identifier == "title":
                i = 0
            elif identifier == "filename":
                i = 1
            elif identifier == "ID":
                i = 2
        except NameError:
            print("Invalid choice of identifier")

    def distance_matrix(self, directed=False, reverse=False):
        """
        Computes distance matrix of graph

        directed -- bool (default False)
                 Consider graph as directed (default False)
        reverse -- bool (default False)
                 reverse direction of graph paths (default False)

        Returns graphs distance matrix
        """
        return shortest_path(
            self.adjacency_matrix(directed=directed, reverse=reverse), directed=directed
        )

    def get_fnames(self, base=True):
        """
        Get filenames of graph

        base -- bool (True)
              basenames of files

        Returns list of filenames
        """
        if base:
            return [os.path.basename(node.fname) for node in self.nodes]

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

    def get_titles(self):
        """
        Returns list of node names (#+title file property)
        """
        return [node.title for node in self.nodes]

    def links(self):
        """
        Returns tuples of (title, links) for each node
        """
        links = [a.get_links() for a in self.nodes]
        return [(a, b) for (a, b) in zip(self.get_titles(), links)]

    def __is_orphan(self, node):
        """
        Checks if node is an orphan with respect to others

        Params:
        node -- node to check orphanhood

        Returns True if node is orphan of self
        """
        pointed_to = True if any(node.id in n.links_to for n in self.nodes) else False
        points_to = node.links_to != {}
        return not points_to and not pointed_to
