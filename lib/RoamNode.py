#!/usr/bin/env python3

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

    def has_tags(self, tags):
        """
        Return true if the node contains any of the tags in `tags`

        Params:
        tags -- list of tags

        Returns:
        True if node contains any of the tags in tags
        """
        return any(tag in tags for tag in self.tags)

    def body(self, fmt = 'raw'):
        """
        Returns full (full-depth) body of node
        """
        body = ""
        for subheading in self.fob.root:
            body += subheading.get_body(format=fmt)

        return body
