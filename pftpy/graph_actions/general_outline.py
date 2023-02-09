from actions import SequenceAction
from graph_actions.generate_graph import GraphInput
from graph_actions.partition import Partition
from graph_actions.contraction import Contraction
from graph_actions.treewidth import Treewidth, WeightedTreewidth
from graph_actions.partition_bags import PartitionBags, PartLargestBag
from graph_actions.graph_stats import GraphStats, GraphStats2


defined_actions = []


class PFlattenedTreewidth(SequenceAction):
    steps = [
        GraphInput,
        Partition, # <- interessanter Schritt
        Contraction,
        WeightedTreewidth,
    ]
defined_actions.append(PFlattenedTreewidth)


class PartitionTreedec(SequenceAction):
    steps = [
        GraphInput,
        Treewidth, # <- interessanter Schritt (gibt es einen besseren Ansatz als HTD/Tamaki?)
        PartitionBags, # <- interessanter Schritt, mit optimaler Lösung vergleichen
    ]
defined_actions.append(PartitionTreedec)

class PartitionOneBag(SequenceAction):
    steps = [
        GraphInput,
        Treewidth, # <- interessanter Schritt (gibt es einen besseren Ansatz als HTD/Tamaki?)
        PartLargestBag, # <- interessanter Schritt, mit optimaler Lösung vergleichen
    ]
defined_actions.append(PartitionOneBag)

class CalcStats(SequenceAction):
    steps = [
        GraphInput,
        GraphStats
    ]

class CalcStats2(SequenceAction):
    steps = [
        GraphInput,
        GraphStats2
    ]
defined_actions.append(CalcStats2)
