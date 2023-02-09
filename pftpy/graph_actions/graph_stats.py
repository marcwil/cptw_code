#!/usr/bin/env python3
from graph_actions.maximal_cliques import MaximalCliques
from actions import Action
import igraph

defined_actions = []

class GraphStats(Action):
    def run(self, graph: igraph.Graph):
        max_cliques = self.retrieve_action(MaximalCliques.name())
        cliques = max_cliques(graph)
        if cliques is not None and len(cliques) > 0:
            num_cliques = len(cliques)
            clique_sizes = [len(c) for c in cliques]
            sum_clique_sizes = sum(clique_sizes)
            largest_clique = max(clique_sizes)
        else:
            num_cliques = -1
            sum_clique_sizes = -1
            largest_clique = -1

        deg_dist = graph.degree_distribution()
        avg_deg = deg_dist.mean
        deg_cov = deg_dist.sd / deg_dist.mean
        clustering = graph.transitivity_undirected()
#        diameter = graph.diameter()
#        print("diameter done")
#        avg_dist = graph.average_path_length()
#        print("path_length done")

        self.set_stat("num_cliques", num_cliques)
        self.set_stat("sum_clique_sizes", sum_clique_sizes)
        self.set_stat("largest_clique", largest_clique)
        self.set_stat("avg_deg", avg_deg)
        self.set_stat("deg_cov", deg_cov)
        self.set_stat("clustering", clustering)
#        self.set_stat("diameter", diameter)
#        self.set_stat("avg_dist", avg_dist)

        return graph

    def get_stat_keys(self):
        return super().get_stat_keys() + [
            "num_cliques",
            "sum_clique_sizes",
            "largest_clique",
            "avg_deg",
            "deg_cov",
            "clustering"
#            "diameter",
#            "avg_dist"
        ]
defined_actions.append(GraphStats)

class GraphStats2(Action):
    def run(self, graph: igraph.Graph):
        htd_action = self.retrieve_action("HTD")
        g,treedec = htd_action(graph)

        largest_cc = -1
        for bag in treedec.vs['vertices']:
            subgraph: igraph.Graph = graph.induced_subgraph(bag)
            clique_count = len(subgraph.maximal_cliques())
            largest_cc = max(clique_count, largest_cc)

        self.set_stat("largest_bag_cc", largest_cc)

        return graph

    def get_stat_keys(self):
        return super().get_stat_keys() + [
            "largest_bag_cc"
        ]
defined_actions.append(GraphStats2)
