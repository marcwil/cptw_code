#!/usr/bin/env python3
from actions import Action
import igraph, collections, numpy as np


defined_actions = []
class Contraction(Action):

    def run(self, old_g: igraph.Graph):
        #Copy the graph so that the initial stays intact (might be useful for
        #stat collection etc)
        # TODO A shallow copy takes barely any time, but
        # there might be a small performance increase when removing it Local
        # testing resulted in ~40ms for a girg/hrg with 1_000_000 vertices
        g: igraph.Graph = old_g.copy()
        c = collections.Counter(g.vs['partition'])
        g.contract_vertices(g.vs['partition'])
        g.simplify()
        #TODO alternate approach: sort the counter's result by index, then
        #calculate and assign weights to the whole list at once
        for v in g.vs:
            v['weight'] = np.log2(c[v.index] + 1)

        # stats
        return g

    def compute_stats(self, input, output):
        self.set_stat('in_n', input.vcount())
        self.set_stat('out_n', output.vcount())

        degs = output.degree()
        self.set_stat('avg_deg', sum(degs) / len(degs))
        self.set_stat('max_deg', max(degs))

        self.set_stat('largest_clique', output.clique_number())

    def get_stat_keys(self) -> 'list[str]':
        return super().get_stat_keys() + [
            'in_n',
            'out_n',
            'avg_deg',
            'max_deg',
            'largest_clique',
        ]
defined_actions.append(Contraction)
