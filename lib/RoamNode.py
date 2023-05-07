#!/usr/bin/env python3

import re

import numpy as np

from orgparse import load as orgload

class RoamNode():
    """Node for org-roam zettels
    """
    def __init__(self, fname):
        super(RoamNode, self).__init__()
        self.fname = fname
        self.fob = orgload(fname)
        self.id = self.fob.get_property('ID')
        self.tags = self.fob.tags
        self.name = self.fob.get_file_property("title")

    def has_exact_tags(self, ex_tags, regex = False):
        """
        Return true if the node contains any of the tags in `tags`

        Params:
        ex_tags -- list of tags to match exactly

        Returns:
        True if node contains any of the tags in tags
        """
        return any(tag in ex_tags for tag in self.tags)


    def has_rx_tags(self, rx_tags, regex = False):
        """
        Return true if the node contains any of the regex tags in `tags`

        Params:
        rx_tags -- list of compiled python regexes to match

        Returns:
        True if node contains any of the regexes in rx_tags
        """
        return any(rx_tag.match(tag) for tag in self.tags for rx_tag in rx_tags)


    def body(self, fmt = 'raw'):
        """
        Returns full (full-depth) body of node
        """
        body = ""
        for subheading in self.fob.root:
            body += subheading.get_body(format=fmt)

        return body
