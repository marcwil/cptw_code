#!/usr/bin/env python3
from actions import Action
import itertools
from math import ceil
import igraph
"""
class Blowup(base.SimpleAction):

    def blowup(g: igraph.Graph):
        g_new = igraph.Graph()
        for v in g.vs:
            #TODO round up correct ??
            amt = int(v['weight']) + 1
            g_new.add_vertices(amt, attributes={ 'origin': v.index } )
            g_new.add_edges( itertools.combinations( g_new.vs.select(origin=v.index), 2) )
        for v1, v2 in itertools.combinations(g.vs, 2):
            if v2 in v1.neighbors():
                g_new.add_edges( itertools.product( g_new.vs.select(origin=v1.index), g_new.vs.select(origin=v2.index) ))
        return g_new

    action = blowup
"""

defined_actions = []

class Blowup(Action):

    def run(self, g: igraph.Graph):
        sequences = []
        origins = []
        counter = 0
        edgelist = []
        for v in g.vs:
            sequences.append([])
            for _ in range(ceil(v['weight'])):
                sequences[-1].append(counter)
                origins.append(v.index)
                counter += 1
            ls = itertools.combinations(sequences[-1], 2)
            edgelist += ls
        for i, j in g.get_edgelist():
            ls = itertools.product( sequences[i], sequences[j] )
            edgelist += ls
        output = igraph.Graph(counter, edges=edgelist, vertex_attrs={'origin': origins})
        self.set_stat('in_n', g.vcount())
        self.set_stat('out_n', output.vcount())
        return output


    def get_stat_keys(self) -> 'list[str]':
        return super().get_stat_keys() + ['in_n', 'out_n']
defined_actions.append(Blowup)
