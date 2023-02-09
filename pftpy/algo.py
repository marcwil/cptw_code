from runner import Runner
from actions import ChoiceAction
from graph_actions.general_outline import (
    PFlattenedTreewidth,
    PartitionTreedec,
    PartitionOneBag,
    CalcStats,
    CalcStats2,
)
#from graph_actions import *
from graph_actions import (
    blowup, contraction, general_outline, generate_graph, greedy_partition,
    partition, partition_bags, treewidth, hitting_set, maximal_cliques
)


all_actions = []
all_actions += blowup.defined_actions
all_actions += contraction.defined_actions
all_actions += general_outline.defined_actions
all_actions += generate_graph.defined_actions
all_actions += greedy_partition.defined_actions
all_actions += partition.defined_actions
all_actions += partition_bags.defined_actions
all_actions += treewidth.defined_actions
all_actions += hitting_set.defined_actions
all_actions += maximal_cliques.defined_actions

import argh

class Algo(ChoiceAction):
    options = {
        "pft": PFlattenedTreewidth,
        "part_treedec": PartitionTreedec,
        "bag": PartitionOneBag,
        "stats": CalcStats,
        "stats2": CalcStats2,
    }

    @staticmethod
    def default_action():
        return 'pft'

all_actions.append(Algo)

runner = Runner("Algo", *all_actions)

argh.dispatch_commands([
    runner.run,
    runner.run_all,
    runner.print,
    runner.print_all
])
