import heapq
from abc import ABC, abstractmethod
from math import ceil
from tempfile import NamedTemporaryFile
import datetime
import random

import igraph, subprocess

from actions import Action, ChoiceAction
from graph_actions.blowup import Blowup


defined_actions = []

def parse_tree_dec(lines):
    index = 0
    line = lines[index]
    while line.startswith('c'):
        # skip comments
        index += 1
        line = lines[index]
    _, _, number_bags, largest_bag, _ = line.split(' ')
    number_bags = int(number_bags)
    largest_bag = int(largest_bag)
    t = igraph.Graph(number_bags)
    t['width'] = largest_bag - 1

    edgelist = []
    for a, b, *c in [line.split(' ') for line in lines[index+1:]]:
        if a == 'c':
            # comment
            continue

        if a == 'b':
            # bag contents
            bag = int(b) - 1
            vertices = [int(v)-1 for v in c]
            t.vs[bag]['vertices'] = vertices
            t.vs[bag]['size'] = len(vertices)
            continue
        else:
            # tree edge
            #t.add_edge(int(a)-1, int(b)-1)
            edgelist.append( (int(a)-1, int(b)-1) )
    t.add_edges(edgelist)
    return t

def annotate_bags(graph, treedec):
    graph.vs['bags'] = [[] for i in range(graph.vcount())]

    for bag in treedec.vs():
        for vert in bag['vertices']:
            graph.vs[vert]['bags'] += [bag.index]
    graph['treewidth'] = treedec['width']


def write_graph(graph, in_stream):
    in_stream.write(f'p tw {graph.vcount()} {graph.ecount()}\n')
    for v, w in graph.get_edgelist():
        in_stream.write(f'{v+1} {w+1}\n')

def failed_treewidth(graph):
    tree = igraph.Graph()
    tree.add_vertex()
    tree.vs[0]['vertices'] = [i for i in range(graph.vcount())]

    graph.vs['bags'] = [0]
    tree['width'] = -1
    graph['treewidth'] = -1
#    from IPython.core.debugger import set_trace; set_trace()
    return graph, tree

def mock_decomposition(graph, width):
    tree = igraph.Graph()
    tree.add_vertex()
    graph['treewidth'] = width
    tree['width'] = width
    return graph, tree


def fill(graph, nodes):
    new_edges = []
    for n1 in nodes:
        for n2 in nodes:
            if n1 >= n2:
                continue
            if not n1 in graph.neighbors(n2):
                new_edges.append((n1, n2))
    graph.add_edges(new_edges)

def elimination_game(graph, order):
    g: igraph.Graph = graph.copy()
    n = g.vcount()
    assert len(order) >= n-1, f"len(order) = {len(order)}, n = {n}"

    rank = [0] * n
    for i, v in enumerate(order):
        rank[v] = i

    # fill edges
    for i, v in enumerate(order):
        neighs = [n for n in g.neighbors(v) if rank[n] > i]
        fill(g, neighs)

    v_to_bags = [list() for _ in range(n)]
    tree: igraph.Graph = igraph.Graph()
    for v in reversed(order):
        # create new bag for last node
        if tree.vcount() == 0:
            tree.add_vertex(vertices=[v])
            v_to_bags[v].append(0)
            continue
        # find smallest parent bag
        neighs = {n for n in g.neighbors(v) if rank[n] > rank[v]}
        chosen_bag = 0
        min_num_other = n
        for neigh in neighs:
            for bag_idx in v_to_bags[neigh]:
                bag_nodes = set(tree.vs[bag_idx]['vertices'])
                if neighs.issubset(bag_nodes):
                    num_other = len(bag_nodes - neighs)
                    if num_other < min_num_other:
                        min_num_other = num_other
                        chosen_bag = bag_idx
        # either add node to parent bag or append new bag with node and neighs
        if min_num_other == 0:
            tree.vs[chosen_bag]['vertices'].append(v)
            v_to_bags[v].append(chosen_bag)
        else:
            bag_nodes = [v] + list(neighs)
            new_bag = tree.add_vertex(vertices=bag_nodes).index
            tree.add_edge(chosen_bag, new_bag)
            v_to_bags[v].append(new_bag)

    width = max(len(bag) for bag in tree.vs['vertices']) - 1
    tree['width'] = width
    graph['treewidth'] = width
    return (graph, tree)


class HTD(Action):
    def __init__(self, context, parents, parameters):
        super().__init__(context, parents, parameters)

        self.dir = self._params['dir']
        self.seed = self._params['seed']
        self.timeout = int(self._params['timeout'])
        self.variant = self._params['variant']
        self.clique_lb = self._params['clique_lb']

    @staticmethod
    def default_params():
        return {
            'dir': './htd/build/bin',
            'seed': random.randint(1, 1e8),
            'timeout': -1,
            'variant': 'default',
            'clique_lb': False,
        }

    def run(self, g: igraph.Graph):
        if self.variant == 'default':
            options = ["--opt", "width", "--strategy", "challenge",
                       "--preprocessing", "advanced", ]
        elif self.variant == 'minfill':
            options = ['--strategy', 'min-fill']
        elif self.variant == 'mindeg':
            options = ['--strategy', 'min-degree']
        else:
            raise KeyError(f"value {self.variant} for parameter variant illegal")
        command = ['./htd_main', "-s",
                   str(self.seed)] + options
        if self.timeout != -1:
            timeout_cmd = ['timeout', '-s', 'QUIT', f'{self.timeout}s']
            command = timeout_cmd + command

        try:
            with subprocess.Popen(command,
                                cwd=self.dir, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL) as p:
                write_graph(g, p.stdin)
                out, err = p.communicate()
        except:
            self.set_stat('status', 'timeout')
            return failed_treewidth(g)
        if p.returncode == 124:
            # timeout
            self.set_stat('status', 'timeout')
            return failed_treewidth(g)
        elif p.returncode != 0:
            self.set_stat('status', 'error')
            return failed_treewidth(g)


        lines = [l.strip() for l in out.splitlines()]
        if len(lines) == 0:
            return failed_treewidth(g)

        t = parse_tree_dec(lines)
        annotate_bags(g, t)
        self.set_stat('status', 'success')

        return (g, t)

    def get_stat_keys(self) -> "list[str]":
        return super().get_stat_keys() + [
            "status"
        ]
defined_actions.append(HTD)


class WeightedMindeg(Action):

    def run(self, graph: igraph.Graph):
        #v['weight']
        n = graph.vcount()
        g = graph.copy()

        degs = []
        for v in g.vs():
            neighs = g.neighbors(v)
            weights = g.vs[neighs]['weight']
            degs.append(sum(weights))

        orig_degs = degs.copy()
        deleted = [False for _ in range(n)]
        num_deleted = 0

        # init pq
        pq = [(degs[i], orig_degs[i], i) for i in range(n)]
        heapq.heapify(pq)

        tw = 1
        order = []

        while g.vcount() - num_deleted > 1:
            # get min deg vertex
            (deg, old_deg, vertex) = heapq.heappop(pq)
            if deg != degs[vertex]:
                continue  # lazy decrease key: degree no longer valid
            order.append(vertex)

            tw = max(tw, deg)

            # fill in neighbourhood, delete v
            neighbors = [w for w in g.neighbors(vertex) if not deleted[w]]
            degree_change = [- g.vs['weight'][vertex]] * len(neighbors)
            edges_add = []
            for i1, n1 in enumerate(neighbors):
                for i2, n2 in enumerate(neighbors):
                    if not n1 < n2:
                        continue
                    if not n1 in g.neighbors(n2):
                        edges_add.append([n1, n2])
                        degree_change[i1] += g.vs['weight'][i2]
                        degree_change[i2] += g.vs['weight'][i1]
            g.add_edges(edges_add)
            for i, neigh in enumerate(neighbors):
                degs[neigh] += degree_change[i]
                heapq.heappush(pq, (degs[neigh], orig_degs[neigh], neigh))
            deleted[vertex] = True
            num_deleted += 1

        t0 = datetime.datetime.now()
        graph, tree = elimination_game(graph, order)
        t1 = datetime.datetime.now()
        delta = t1 - t0
        self.set_stat('time_elimination_game', delta.total_seconds())
        self.set_stat('elimination_width', graph['treewidth'])
        tree['width'] = tw
        graph['treewidth'] = tw
        return graph, tree

    def get_stat_keys(self):
        return super().get_stat_keys() + [
            'time_elimination_game',
            'elimination_width'
        ]
defined_actions.append(WeightedMindeg)


class CliqueGreedy(Action):

    def run(self, graph: igraph.Graph):
        n = graph.vcount()
        partition = self.retrieve_action("Partition")

        g = partition(graph)
        g.vs['deleted'] = [False for _ in range(n)]

        order = []
        deleted = [False for _ in range(n)]
        num_deleted = 0

        while n - num_deleted > 1:
            min_vert = -1
            min_neighs = []
            num_parts = n
            for v in g.vs.select(deleted=False):
                neighs = [n for n in g.neighbors(v.index) if not g.vs[n]['deleted']]
                partitions = {g.vs[n]['partition'] for n in neighs}
                if len(partitions) < num_parts:
                    num_parts = len(partitions)
                    min_vert = v.index
                    min_neighs = neighs

            order.append(min_vert)
            g.vs[min_vert]['deleted'] = True
            num_deleted += 1
            fill(g, min_neighs)

        graph, tree = elimination_game(graph, order)
        return graph, tree
defined_actions.append(CliqueGreedy)


class IterativeCliqueGreedy(Action):

    def run(self, graph: igraph.Graph):
        n = graph.vcount()
        partition = self.retrieve_action("Partition")

        g: igraph.Graph = partition(graph)
        g.vs['deleted'] = [False for _ in range(n)]

        order = []
        num_deleted = 0

        while n - num_deleted > 1:
            min_vert = -1
            min_neighs = []
            num_parts = n
            for v in g.vs.select(deleted=False):
                neighs = [n for n in g.neighbors(v.index) if not g.vs[n]['deleted']]
                induced = g.induced_subgraph(neighs + [v])
                ind_n, ind_m = induced.vcount(), induced.ecount()
                if ind_m == ind_n*(ind_n-1) // 2:
                    partitions = 1
                else:
                    partitioned: igraph.Graph = partition(induced)
                    partitions = len(set(partitioned.vs['partition']))
                if partitions < num_parts:
                    num_parts = partitions
                    min_vert = v.index
                    min_neighs = neighs
            order.append(min_vert)
            g.vs[min_vert]['deleted'] = True
            num_deleted += 1
            fill(g, min_neighs)


        graph, tree = elimination_game(graph, order)
        return graph, tree
defined_actions.append(IterativeCliqueGreedy)



class Treewidth(ChoiceAction):
    options = {
        'htd': HTD,
        'clique_greedy': CliqueGreedy,
        'iter_clique_greedy': IterativeCliqueGreedy,
    }

    @classmethod
    def default_action(cls):
        return 'htd'

    def compute_stats(self, input, output) -> 'dict[str,str]':
        graph, tree = output
        self.set_stat('treewidth', graph['treewidth'])
        self.set_stat('num_bags', tree.vcount())

    def get_stat_keys(self) -> "list[str]":
        return super().get_stat_keys() + [
            "treewidth",
            "num_bags"
        ]
defined_actions.append(Treewidth)


class BlowupTreewidth(Action):

    def run(self, g: igraph.Graph):
        blowup = self.retrieve_action("Blowup")
        blowed_up = blowup(g)

        treewidth = self.retrieve_action("Treewidth")
        res = treewidth(blowed_up)
        assert(blowed_up.vcount() > 0)
        assert(res is not None)

        return res
defined_actions.append(BlowupTreewidth)


class WeightedTreewidth(ChoiceAction):

    options = {
        'blowup_tw': BlowupTreewidth,
        'weighted_mindeg': WeightedMindeg,
#        'weighted_minfill': WeightedMinfill,
    }

    @staticmethod
    def default_action():
        return 'blowup_tw'

    def compute_stats(self, input, output):
        graph, tree = output
        self.set_stat('width', graph['treewidth'])

    def get_stat_keys(self) -> "list[str]":
        return super().get_stat_keys() + ["treewidth"]
defined_actions.append(WeightedTreewidth)
