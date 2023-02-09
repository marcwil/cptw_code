#!/usr/bin/env python3
from datetime import datetime
import numpy as np
from math import log2
from actions import Action, ActionContext
from graph_actions.partition import BranchingPartition
import igraph

defined_actions = []

class PartitionBags(Action):
    def __init__(self, context, parents, parameters):
        super().__init__(context, parents, parameters)
        self.partition: Action = None  # has to be set using set_partition

        self.product_weight = 0

        self._num_partitions = []
        self._num_clq_red = 0

        self.other_stats = ["num_branching", "num_leaves", "num_lb_reductions",
                            "num_lb2_reductions", "num_sw_reductions", "input_cliques"]
        self._stat_dict = {var: [] for var in self.other_stats}

        self.verbose = self._params['verbose']
        self.sufficient_weight = self._params['sufficient_weight']
        self.timeout = int(self._params['timeout'])
        self.start_time = datetime.now()


    @staticmethod
    def default_params():
        return {
            'verbose': False,
            'sufficient_weight': True,
            'timeout': -1
        }

    def set_partition(self, partition):
        self.partition = partition

    def timeout_exceeded(self):
        if self.timeout == -1:
            return False
        t1 = datetime.now()
        delta = t1 - self.start_time
        return delta.total_seconds() > self.timeout

    def weight(self, graph, bag):
        contraction = self.retrieve_action("Contraction")

        subgraph: igraph.Graph = graph.induced_subgraph(bag)
        n, m = subgraph.vcount(), subgraph.ecount()
        if m == n*(n-1) // 2:
            self._num_partitions.append(1)
            self._num_clq_red += 1
            res = log2(n+1)
        else:
            partitioned = None
            if self.sufficient_weight is True:
                if self.product_weight != 0 and isinstance(self.partition.option, BranchingPartition):
                    partitioned = self.partition([subgraph, {
                        'sufficient_weight': self.product_weight
                    }])
            if partitioned is None:
                partitioned = self.partition(subgraph)

            if self.timeout_exceeded() or self.partition.get_stat('status') == 'timeout':
                self.set_stat('status', 'timeout')
                return -1

            if isinstance(self.partition.option, BranchingPartition):
                curr_prod_weight = self.partition.get_stat('product_weight')
                self.product_weight = max(self.product_weight, curr_prod_weight)

            contracted = contraction(partitioned)

            self._num_partitions.append(contracted.vcount())
            if isinstance(self.partition.option, BranchingPartition):
                for key in self.other_stats:
                    self._stat_dict[key].append(self.partition.option.stats[key])
            res = sum(contracted.vs['weight'])
        return res

    def run(self, in_args):
        self.start_time = datetime.now()
        self.set_stat('status', 'init')

        graph, tree = in_args
        if graph['treewidth'] == -1:
            # previous fail
            self.set_stat('status', 'failed')
            return graph, tree
        bags = list(enumerate(tree.vs['vertices']))
        # sort bags descending by size
        bags.sort(key=lambda pair: len(pair[1]), reverse=True)

        max_weight = 0
        max_idx = -1
        weights = []
        for i, bag in bags:
            w = self.weight(graph, bag)
            weights.append(w)
            if w > max_weight:
                max_weight = w
                max_idx = i
            if self.get_stat('status') == "timeout":
                self.set_stat('max_weight', -1)
                return graph, tree
        self.set_stat('status', "success")
        tree.vs['weights'] = weights
        graph['max_weight'] = max_weight

        if self.verbose:
            print(f"weight = {max_weight}, bag {max_idx} {bags[max_idx]}")
            bag_sizes = np.array([len(bag) for bag in bags])
            print(f"bag size: max {bag_sizes.max()} mean {bag_sizes.mean()} median {np.median(bag_sizes)}")

        self.set_stat('max_weight', max_weight)

        return graph, tree

    def compute_stats(self, input, output) -> 'dict[str,str]':
        graph, tree = output
        partition_nums = np.array(self._num_partitions)
        mean_partition_num = str(partition_nums.mean())
        max_partition_num = str(np.max(partition_nums, initial=-1))
        median_partition_num = str(np.median(partition_nums))
        self.set_stat('mean_partition_num', mean_partition_num)
        self.set_stat('median_partition_num', median_partition_num)
        self.set_stat('max_partition_num', max_partition_num)
        self.set_stat('partition_option', str(self.partition))

        self.set_stat('num_clq_red', self._num_clq_red)
        for key in self.other_stats:
            array = np.array(self._stat_dict[key])
            if len(array > 0):
                total_sum = array.sum()
                max_val = np.max(array)
                mean_val = array.mean()
                median_val = np.median(array)
                self.set_stat(f'{key}_sum', str(total_sum))
                self.set_stat(f'{key}_max', str(max_val))
                self.set_stat(f'{key}_mean', str(mean_val))
                self.set_stat(f'{key}_median', str(median_val))
            else:
                self.set_stat(f'{key}_sum', -1)
                self.set_stat(f'{key}_max', -1)
                self.set_stat(f'{key}_mean', -1)
                self.set_stat(f'{key}_median', -1)

    def get_stat_keys(self) -> "list[str]":
        res = super().get_stat_keys() + [
            "status",
            "max_weight",
            "mean_partition_num",
            "median_partition_num",
            "max_partition_num",
            "num_clq_red",
            "partition_option",
        ]
        for key in self.other_stats:
            res.append(f'{key}_sum')
            res.append(f'{key}_max')
            res.append(f'{key}_mean')
            res.append(f'{key}_median')
        return res

    @classmethod
    def construct(cls, context: ActionContext, parents):
        instance = super().construct(context, parents)
        part = context.construct_action("Partition", parents + [cls.name()])
        instance.set_partition(part)
        return instance

    @classmethod
    def construct_all(cls, context: ActionContext, parents):
        partition_choices = context.construct_variants("Partition", parents + [cls.name()])
        res = []
        for part in partition_choices:
            for inst in super().construct_all(context, parents):
                inst.set_partition(part)
                res.append(inst)
        return res
defined_actions.append(PartitionBags)

class PartLargestBag(PartitionBags):
    def run(self, in_args):
        graph, tree = in_args
        bags = tree.vs['vertices']
        largest = max(bags, key=lambda b: len(b))
        weight = self.weight(graph, largest)
        tree.vs['weights'] = [weight for bag in bags]
        graph['max_weight'] = weight

        self.set_stat('max_weight', weight)

        return graph, tree

    def compute_stats(self, input, output) -> 'dict[str,str]':
        graph, tree = output
        partition_nums = np.array(self._num_partitions)
        mean_partition_num = str(partition_nums.mean())
        max_partition_num = str(partition_nums.max())
        median_partition_num = str(np.median(partition_nums))

        self.set_stat('mean_partition_num', mean_partition_num)
        self.set_stat('median_partition_num', median_partition_num)
        self.set_stat('max_partition_num', max_partition_num)
        self.set_stat('partition_option', str(self.partition))

        for key, val in self.partition.option.stats.items():
            self.set_stat(f'partition:{key}', val)

    def get_stat_keys(self) -> "list[str]":
        return super().get_stat_keys() + [
            "status",
            "max_weight",
            "mean_partition_num",
            "median_partition_num",
            "max_partition_num",
            "partition_option",
        ]
defined_actions.append(PartLargestBag)
