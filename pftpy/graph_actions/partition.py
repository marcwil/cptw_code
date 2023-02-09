from datetime import datetime
from actions import Action, SequenceAction, ChoiceAction
from graph_actions.greedy_partition import MaximalIS, AssignVertices
import igraph, operator, collections, statistics
import numpy as np
from math import log2
from bisect import bisect
from sys import setrecursionlimit

import heapq

setrecursionlimit(1<<20)

defined_actions = []


class Greedy(SequenceAction):

    steps = [
        MaximalIS,
        AssignVertices,
    ]


defined_actions.append(Greedy)


class LargestCliqueRepeat(Action):

    def run(self, g: igraph.Graph):
        copy = g.copy()
        copy.vs['idx'] = [i for i in range(g.vcount())]

        part = 0
        while copy.vcount() > 0:
            cliques = copy.maximal_cliques()
            largest = max(cliques, key=lambda c: len(c))
            largest_idx = copy.vs[largest]['idx']
            g.vs[largest_idx]['partition'] = part
            part += 1
            copy.delete_vertices(largest)
        return g


defined_actions.append(LargestCliqueRepeat)


class FastLargestCliqueBad(Action):

    def run(self, g: igraph.Graph):
        n = g.vcount()
        cliques = g.maximal_cliques()
        deleted = [False] * n
        sizes = [len(c) for c in cliques]

        c_of_v = [list() for v in g.vs()]
        for i, c in enumerate(cliques):
            for v in c:
                c_of_v[v].append(i)  # v is in clique with index i

        # init pq
        pq = [(n-size, i) for i, size in enumerate(sizes)]
        heapq.heapify(pq)

        assigned = 0
        i = 0
        while assigned < n:
            # find largest clique c
            (comp_size, clq_i) = heapq.heappop(pq)
            clq_size = n - comp_size
            if clq_size != sizes[clq_i]:
                continue  # lazy decrease key: clique size no longer valid


            # assign vertices to c
            changed_cliques = []
            assigned += clq_size
            for v in cliques[clq_i]:
                if deleted[v]:
                    continue
                deleted[v] = True

                g.vs[v]['partition'] = i
                for c in c_of_v[v]:
                    sizes[c] -= 1
                    changed_cliques += [c]

            # update pq
            for c in set(changed_cliques):
                size = sizes[c]
                if size > 0:
                    heapq.heappush(pq, (n - size, c))

            i += 1
        return g


defined_actions.append(FastLargestCliqueBad)


class CliquePriorityQueue():
    def __init__(self, graph):
        self.n = graph.vcount()
        self.cliques = graph.maximal_cliques()
        self.deleted = [False] * self.n
        self.sizes = [len(c) for c in self.cliques]
        self.orig_sizes = [s for s in self.sizes]

        # list mapping vertices to their cliques
        self.c_of_v = [list() for v in graph.vs()]
        for i, c in enumerate(self.cliques):
            for v in c:
                self.c_of_v[v].append(i)  # v is in clique with index i

        # init pq
        self.pq = [(self.n-size, self.n-size, i) for i, size in enumerate(self.sizes)]
        heapq.heapify(self.pq)

    def next_largest_clique(self):
        while len(self.pq) > 0:
            (comp_size, _, clq_i) = heapq.heappop(self.pq)
            clq_size = self.n - comp_size
            if clq_size != self.sizes[clq_i]:
                continue  # lazy decrease key: clique size no longer valid

            return clq_i
        return None

    def remaining_vertices(self, clq_index):
        return [v for v in self.cliques[clq_index] if not self.deleted[v]]

    def update_assigned_vertices(self, assigned):
        # assign vertices to c
        changed_cliques = []
        for v in assigned:
            if self.deleted[v]:
                continue
            self.deleted[v] = True

            for c in self.c_of_v[v]:
                self.sizes[c] -= 1
                changed_cliques += [c]

        # update pq
        for c in set(changed_cliques):
            size = self.sizes[c]
            orig_size = self.orig_sizes[c]
            if size > 0:
                heapq.heappush(self.pq, (self.n - size, self.n - orig_size, c))


class FastLargestClique(Action):

    def run(self, graph: igraph.Graph):
        g = graph.copy()
        cpq = CliquePriorityQueue(g)

        num_assigned = 0
        i = 0
        while num_assigned < cpq.n:
            # find largest clique c
            clq_i = cpq.next_largest_clique()
            clique = cpq.remaining_vertices(clq_i)

            num_assigned += len(clique)
            g.vs[clique]['partition'] = i
            i += 1
            cpq.update_assigned_vertices(clique)
        return g


defined_actions.append(FastLargestClique)


# This is a specific method that is only applicable to hrg graphs which have the
# 'r' attribute (through setting the -coords argument)
class MaxRadiusFullNeighborhood(Action):

    def run(self, g: igraph.Graph):

        #operator.itemgetter('r') returns a function equivalent to ['r']
        vertices = sorted(g.vs, key=operator.itemgetter('r'), reverse=True)

        g.vs['partition'] = None
        i = 0

        for v in vertices:
            if v['partition'] is not None:
                continue
            v['partition'] = i
            g.vs.select( g.neighbors(v) ).select(partition=None)['partition'] = i
            i = i + 1
        return g


defined_actions.append(MaxRadiusFullNeighborhood)


class CliqueAndRadius(Action):

    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

        self._modulus = int(self._params['modulus'])

    @staticmethod
    def default_params():
        return {
            'modulus': 3
        }

    def run(self, graph: igraph.Graph):
        g = graph.copy()
        cpq = CliquePriorityQueue(g)

        radius_pq = [(-v['r'], v.index) for v in g.vs]
        heapq.heapify(radius_pq)

        num_assigned = 0
        next_partition = 0
        while num_assigned < cpq.n:
            if next_partition % self._modulus == 0:
                # find largest clique c
                clq_i = cpq.next_largest_clique()
                partition = cpq.remaining_vertices(clq_i)
            else:
                # find next vertex with largest radius
                vertex = None
                while vertex is None:
                    (neg_r, v_ind) = heapq.heappop(radius_pq)
                    if not cpq.deleted[v_ind]:
                        vertex = v_ind
                        break
                neighs = g.neighborhood(vertex)
                partition = [neigh for neigh in neighs if not cpq.deleted[neigh]]

            num_assigned += len(partition)
            g.vs[partition]['partition'] = next_partition
            next_partition += 1
            cpq.update_assigned_vertices(partition)
        return g
defined_actions.append(CliqueAndRadius)


class MinHSPartition(Action):
    """
    Minimum Hitting Set partition
    """

    def __init__(self, context, parents=None, params=None):
        super().__init__(context, parents, params)
        # get hitting set solver
        self.HS = self.retrieve_action("HittingSet")

    @staticmethod
    def make_hyp(graph, cliques):
        n = len(cliques)
        cliques = [set(c) for c in cliques]
        edges = []

        for graph_i in range(graph.vcount()):
            edge = []
            for clq_i, clq in enumerate(cliques):
                if graph_i in clq:
                    edge.append(clq_i)
            if len(edge) > 0:
                edges.append(edge)
        return n, edges

    @staticmethod
    def assign_partitions(graph, cliques, solution):
        n = graph.vcount()
        num_partitions = len(solution)

        partitions_of_v = [list() for _ in range(n)]

        for clq_i in solution:
            for v in cliques[clq_i]:
                partitions_of_v[v].append(clq_i)

        chosen_partition = []
        for vertex in range(n):
            parts = partitions_of_v[vertex]
            best_partition = max(parts, key=lambda p: len(cliques[p]))
            chosen_partition.append(best_partition)

        mapper = {p: i for (i, p) in enumerate(set(chosen_partition))}
        graph.vs['partition'] = [mapper[p] for p in chosen_partition]
        return graph

    def run(self, input: igraph.Graph):
        graph = input.copy()
        cliques = graph.maximal_cliques()
        hyp = self.make_hyp(graph, cliques)

        # call hitting set solver
        solution = self.HS(hyp)
        self.set_stat('hs_size', len(solution))
        self.set_stat('status', self.HS.get_stat('status'))
        if self.get_stat('status') != 'success':
            return []

        res = self.assign_partitions(graph, cliques, solution)
        return res

    def get_stat_keys(self):
        return super().get_stat_keys() + ["hs_size", "status"]

    def __str__(self):
        res = super().__str__() + "(" + self.HS.__str__() + ")"
        return res
defined_actions.append(MinHSPartition)


class WeightedHSPartition(Action):
    """
    Weighted Hitting Set partition
    """

    @staticmethod
    def calc_weights(cliques):
        return [log2(len(c)+1) for c in cliques]

    def run(self, input: igraph.Graph):
        graph = input.copy()
        cliques = graph.maximal_cliques()
        _, edges = MinHSPartition.make_hyp(graph, cliques)
        weights = self.calc_weights(cliques)
        hyp = (weights, edges)

        # get hitting set solver
        HS = self.retrieve_action("HittingSet")
        solution = HS(hyp)
        self.set_stat('hs_size', len(solution))
        self.set_stat('status', HS.get_stat('status'))
        if self.get_stat('status') != 'success':
            return []

        res = MinHSPartition.assign_partitions(graph, cliques, solution)
        return res

    def get_stat_keys(self):
        return super().get_stat_keys() + ["hs_size", "status"]
defined_actions.append(WeightedHSPartition)


class BFPartition(Action):
    """
    Brute-Force Optimal Partition
    """
    def solve_rec(self, graph: igraph.Graph, upper_bound=-1, max_size=-1):
        if upper_bound == -1:
            upper_bound = 2**graph.vcount()
        if max_size == -1:
            max_size = graph.vcount()

        cliques = graph.maximal_cliques()
        cliques.sort(key=lambda c: len(c), reverse=True)

        if len(cliques) == 1:  # base case
            solution = graph.vs['idx']
            return [solution], len(solution)+1

        num_large = graph.vcount() // max_size
        remaining = graph.vcount() % max_size
        minimum_weight = (max_size+1)**num_large * (remaining + 1)
        if minimum_weight > upper_bound:
            return [], -1

        sol = None
        min_weight = 2**(graph.vcount()*2)

        for i, clq in enumerate(cliques):
            if len(clq) <= max_size:
                rec_graph = graph.copy()
                rec_graph.delete_vertices(clq)
                new_bound = upper_bound // (len(clq)+1)
                rec_sol, rec_weight = self.solve_rec(rec_graph, new_bound, len(clq))
                if rec_weight == -1:
                    continue
                chosen = graph.vs[clq]['idx']
                solution = [chosen] + rec_sol
                weight = rec_weight * (len(chosen)+1)
                if weight < min_weight:
                    sol = solution
                    min_weight = weight
                    if min_weight < upper_bound:
                        upper_bound = min_weight

        if sol is None:
            return [], -1
        return sol, min_weight

    def run(self, input: igraph.Graph):
        graph = input.copy()
        graph.vs['idx'] = [i for i in range(graph.vcount())]
        solution, weight = self.solve_rec(graph)
        assert len(solution) > 0
        for i, clq in enumerate(solution):
            graph.vs[clq]['partition'] = i
        return graph
defined_actions.append(BFPartition)

class BranchingPartition(Action):
    """
    Brute-Force Optimal Partition with Branching (v2)
    """
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

        self.reduction_sw = self._params['sufficient_weight']
        self.reduction_lb = self._params['lower_bound']
        self.reduction_lb2 = self._params['lower_bound2']

        self.timeout = int(self._params['timeout'])
        self.start_time = datetime.now()
        self.best_upper = -1
        self.best_lower = -1
        self.exit_status = "init"  # will have value 'success' or 'timeout' after being called

        self.input_cliques = 0

        self.num_sw_red = 0
        self.num_lb_red = 0
        self.num_lb2_red = 0
        self.num_branching = 0
        self.num_leaves = 0
        self.num_long_paths = 0
        self.num_dead_end = 0

    def reset_counters(self):
        self.best_upper = -1
        self.best_lower = -1
        self.exit_status = "init"  # will have value 'success' or 'timeout' after being called
        self.input_cliques = 0
        self.num_sw_red = 0
        self.num_lb_red = 0
        self.num_lb2_red = 0
        self.num_branching = 0
        self.num_leaves = 0
        self.num_long_paths = 0
        self.num_dead_end = 0


    @staticmethod
    def default_params():
        return {
            'sufficient_weight': True,
            'lower_bound': True,
            'lower_bound2': True,
            'timeout': -1,  # timeout in seconds; -1 for no timeout
        }

    @staticmethod
    def weight(solution):
        res = 1
        for s in solution:
            res = res * (len(s) + 1)
        return res

    @staticmethod
    def product(arr):
        res = 1
        for num in arr:
            res *= num
        return res


    def timeout_exceeded(self):
        if self.timeout == -1:
            return False
        now = datetime.now()
        delta = now - self.start_time
        if delta.total_seconds() > self.timeout:
            self.exit_status = 'timeout'
            return True
        return False


    def solve_rec(self, graph: igraph.Graph, **kwargs):
        if self.timeout_exceeded():
            return [], -1
        cliques = graph.maximal_cliques()
        cliques.sort(key=lambda c: len(c), reverse=True)
        if len(cliques) > self.input_cliques:
            self.input_cliques = len(cliques)

        if 'partial_sol' in kwargs:
            partial_sol = kwargs['partial_sol']
        else:
            partial_sol = []
        partial_weight = self.weight(partial_sol)

        # base case
        if len(cliques) == 1:
            solution = partial_sol + [graph.vs['idx']]
            self.num_leaves += 1
            self.num_long_paths += 1
            return solution, self.weight(solution)
        if len(cliques) == 2:
            c1 = cliques[0]
            c2 = list(set(cliques[1]) - set(c1))
            last_two = [graph.vs[clq]['idx'] for clq in [c1, c2]]
            solution = partial_sol + last_two
            self.num_leaves += 1
            self.num_long_paths += 1
            return solution, self.weight(solution)

        # solutions below this value should get accepted immediately
        sufficient_weight = kwargs.get('sufficient_weight', -1)
        # only use cliques up to max_size
        max_size = kwargs.get('max_size', graph.vcount())
        max_size = min(max_size, graph.vcount())
        # don't search solutions worse than upper_bound
        upper_bound = kwargs.get('upper_bound', 2**graph.vcount()+1)

        # lower bound 1: max size
        if self.reduction_lb == True:
            num_large = graph.vcount() // max_size  # how many times does the largest possible clique fit?
            remainder = graph.vcount() % max_size
            additional_weight = (max_size+1)**num_large * (remainder + 1)
            lower_bound = partial_weight * additional_weight
            if upper_bound != -1 and lower_bound > upper_bound:
                self.num_lb_red += 1
                self.num_leaves += 1
                return [], -1

        lower_bound2 = 0
        # lower bound 2: size packing
        if self.reduction_lb2 == True:
            to_be_covered = graph.vcount()
            num_covered = 0
            chosen_sizes = []
            current_upper_bound = max_size

            sizes = [len(c) for c in cliques]
            sizes.reverse()  # now sorted ascending

            # index of largest clique that is smaller than the upper bound
            largest_below_up = bisect(sizes, max_size) - 1
            mod_below_up = largest_below_up+1  # next clique that might be below
                                               # upper bound after subtracting
                                               # num_covered
            # add one virtual clique that cannot be picked
            sizes.append(3*graph.vcount()+10)

            failed = False
            while num_covered < to_be_covered:
                mod_size = sizes[mod_below_up] - num_covered
                if mod_size <= current_upper_bound:
                    assert sizes[mod_below_up] != 3*graph.vcount()+10
                    chosen_weight = current_upper_bound
                    mod_below_up += 1
                elif largest_below_up >= 0:
                    # use small
                    chosen_weight = sizes[largest_below_up]
                    largest_below_up -= 1
                else:
                    # cannot select large or small clique :(
                    failed = True
                    break

                # choose clique
                chosen_weight = min(chosen_weight, to_be_covered - num_covered)
                chosen_sizes.append(chosen_weight)
                num_covered += chosen_weight
                current_upper_bound = min(current_upper_bound, chosen_weight)

            additional_weight = self.product([s+1 for s in chosen_sizes])
            lower_bound2 = partial_weight * additional_weight
            if upper_bound != -1 and (lower_bound2 > upper_bound or failed):
                self.num_lb2_red += 1
                self.num_leaves += 1
                return [], -1

        # collect best known bounds so far, before checking timeout
        if not self.reduction_lb and not self.reduction_lb2:
            lower_bound2 = 0
        if self.best_lower == -1 or self.best_lower < lower_bound2:
            self.best_lower = lower_bound2
        if self.best_upper == -1 or self.best_upper > upper_bound:
            self.best_upper = upper_bound
        # check timeout
        if self.timeout_exceeded():
            return [], -1


        sol = None
        min_weight = partial_weight * 2**(graph.vcount())+1

        small_cliques = [c for c in cliques if len(c) <= max_size]
        if len(small_cliques) > 1:
            self.num_branching += 1
        for clq in small_cliques:
            if self.timeout_exceeded():
                break
            rec_graph = graph.copy()
            rec_graph.delete_vertices(clq)
            chosen = graph.vs[clq]['idx']
            new_partial_sol = partial_sol + [chosen]
            args = {
                'partial_sol': new_partial_sol,
                'max_size': len(clq),
                'sufficient_weight': sufficient_weight,
                'upper_bound': upper_bound,
            }
            rec_sol, rec_weight = self.solve_rec(rec_graph, **args)
            if rec_weight == -1:
                continue
            if rec_weight < min_weight:
                sol = rec_sol
                min_weight = rec_weight
                if min_weight < upper_bound:
                    upper_bound = min_weight
            if self.reduction_sw == True and rec_weight < sufficient_weight:
                self.num_sw_red += 1
                self.num_leaves += 1
                return rec_sol, rec_weight

        self.num_leaves += 1
        self.num_dead_end += 1
        if sol is None:
            return [], -1
        return sol, min_weight

    def run(self, input: igraph.Graph):
        self.reset_counters()
        self.start_time = datetime.now()
        if isinstance(input, list):
            graph = input[0].copy()
            hints = input[1]
        else:
            graph = input.copy()
            hints = {}

        sufficient_weight = hints.get('sufficient_weight', -1)

        graph.vs['idx'] = [i for i in range(graph.vcount())]
        solution, weight = self.solve_rec(graph, sufficient_weight=sufficient_weight)
        if self.exit_status == 'timeout':
            if self.best_lower > 0:
                lower = log2(self.best_lower)
            else:
                lower = -1
            if self.best_upper > 0:
                upper = log2(self.best_upper)
            else:
                upper = -1
            self.set_stat('product_weight', lower)
            self.set_stat('lower_bound', upper)
            self.set_stat('status', 'timeout')
            return graph
        else:
            self.set_stat('product_weight', weight)
            self.set_stat('lower_bound', weight)
            self.set_stat('status', 'success')
            assert len(solution) > 0, f'solution, weight: {solution, weight}'
            for i, clq in enumerate(solution):
                graph.vs[clq]['partition'] = i
            return graph

    def compute_stats(self, input, output):
        self.set_stat('num_branching', self.num_branching)
        self.set_stat('num_leaves', self.num_leaves)
        self.set_stat('num_long_paths', self.num_long_paths)
        self.set_stat('num_dead_end', self.num_dead_end)
        self.set_stat('num_lb_reductions', self.num_lb_red)
        self.set_stat('num_lb2_reductions', self.num_lb2_red)
        self.set_stat('num_sw_reductions', self.num_sw_red)
        self.num_reductions = self.num_lb_red + self.num_lb2_red + self.num_sw_red
        self.set_stat('input_cliques', self.input_cliques)

    def get_stat_keys(self) -> 'list[str]':
        res = super().get_stat_keys()
        return res + [
            'product_weight',
            'status',
            'lower_bound',
            'num_branching',
            'num_leaves',
            'num_long_paths',
            'num_lb_reductions',
            'num_lb2_reductions',
            'num_sw_reductions',
            'num_dead_end',
            'input_cliques'
        ]
defined_actions.append(BranchingPartition)


class Partition(ChoiceAction):
    """Partition actions take a graph (igraph.Graph) and return a copy(?) of
    the graph with an added vs['partition'] attribute to the vertices.
    The partitions should be numbers in 0,...,num_partitions-1.
    """

    options = {
        'greedy': Greedy,
        'flc': FastLargestClique,
        'flcb': FastLargestCliqueBad,
        'car': CliqueAndRadius,
        'lc_repeat': LargestCliqueRepeat,
        'max_radius': MaxRadiusFullNeighborhood,
        'hs': MinHSPartition,
        'whs': WeightedHSPartition,
        'bf': BFPartition,
        'branch': BranchingPartition,
    }

    @staticmethod
    def default_action():
        return "flc"

    def compute_stats(self, input, output) -> 'dict[str,str]':
        if 'status' in self.option._stats:
            self.set_stat('status', self.option.get_stat('status'))
        else:
            self.set_stat('status', 'success')

        if self.get_stat('status') == 'success' and output is not None:
            counter = collections.Counter(output.vs['partition'])
        else:
            counter = collections.Counter([-1])

        sizes = [v for _, v in counter.most_common()]
        self.set_stat('amount', len(sizes))
        self.set_stat('largest', sizes[0])
        self.set_stat('smallest', sizes[-1])
        self.set_stat('median', statistics.median(sizes))
        self.set_stat('average', statistics.mean(sizes))

    def get_stat_keys(self) -> 'list[str]':
        res = super().get_stat_keys()
        return res + [
            'status',
            'amount',
            'largest',
            'smallest',
            'median',
            'average']


defined_actions.append(Partition)
