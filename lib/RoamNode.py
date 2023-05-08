#!/usr/bin/env python3

import re

import numpy as np

class RoamNode():
    """Node for org-roam zettels
    """
    def __init__(self, fname, title, id, tags, links_to):
        super(RoamNode, self).__init__()
        self.fname = fname
        # self.fob = orgload(fname)
        self.title = title
        self.id = id
        self.tags = tags
        self.links_to = links_to


    def links_to(self, other_id):
        return other_id in links_to

    def tags(self):
        return self.tags

    def links(self,n):
        return n.get_id() in self.links_to

    def get_id(self):
        return self.id

    def get_links(self):
        return self.links_to

    def is_orphan(self , others):
        """
        Checks if node is an orphan with respect to others

        Params:
        other -- iterable of nodes to check against

        Returns True if node is orphan
        """
        is_pointed_to = True if any(self.id in a.get_links() for a in others) else False
        points_to = self.links_to != {}
        return not points_to and not is_pointed_to

    def has_tag(self, tags_checked):
        return any(tag in tags_checked for tag in self.tags)

    def has_regex_tag(self, rxs):
        return any(rx.match(tag) for tag in self.tags for rx in rxs)

    def __str__(self):
        return f"({self.title}, {self.id})"

    def __repr__(self):
        return  f"({self.title}, {self.id})"


    # def has_exact_tags(self, ex_tags, regex = False):
    #     """
    #     Return true if the node contains any of the tags in `tags`

    #     Params:
    #     ex_tags -- list of tags to match exactly

    #     Returns:
    #     True if node contains any of the tags in tags
    #     """
    #     return any(tag in ex_tags for tag in self.tags)


    # def has_rx_tags(self, rx_tags, regex = False):
    #     """
    #     Return true if the node contains any of the regex tags in `tags`

    #     Params:
    #     rx_tags -- list of compiled python regexes to match

    #     Returns:
    #     True if node contains any of the regexes in rx_tags
    #     """
    #     return any(rx_tag.match(tag) for tag in self.tags for rx_tag in rx_tags)


    # def body(self, fmt = 'raw'):
    #     """
    #     Returns full (full-depth) body of node
    #     """
    #     body = ""
    #     for subheading in self.fob.root:
    #         body += subheading.get_body(format=fmt)

    #     return body
