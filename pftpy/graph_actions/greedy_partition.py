import random
import igraph
from actions import Action, ChoiceAction

defined_actions = []

class GreedyIS(Action):

    def run(self, g: igraph.Graph) -> igraph.Graph:
        g.vs['candidate'] = True
        g.vs['in_is'] = False
        while g.vs.select(candidate=True):
            v = g.vs.find(candidate=True)
            v['in_is'] = True
            v['candidate'] = False
            for v_n in v.neighbors():
                v_n['candidate'] = False
        del g.vs['candidate']
        return g


defined_actions.append(GreedyIS)

## TODO wip
#class BuiltInIS(base2.Action):
#
#    @staticmethod
#    def generate_is(g: igraph.Graph) -> igraph.Graph:
#        g.vs['in_is'] = False


class MaximalIS(ChoiceAction):

    options = {
        'pure_greedy': GreedyIS,
        #min degree greedy
    }

    def compute_stats(self, input, output) -> "dict[str,str]":
        self._stats["size"] = len(output.vs.select(in_is=True))

    def get_stat_keys(self) -> "list[str]":
        return super().get_stat_keys() + ["size"]



defined_actions.append(MaximalIS)

# The actions above build an IS on the graph by assigning True or False to a 'in_is' attribute of each vertex

class AssignGreedy(Action):

    def run(self, g: igraph.Graph):
        for i, v in enumerate(g.vs.select(in_is=True)):
            v['partition'] = i
        for v in g.vs.select(in_is=False):
            for v_n in v.neighbors():
                if v_n['in_is']:
                    v['partition'] = v_n['partition']
                    break
        del g.vs['in_is']
        return g


defined_actions.append(AssignGreedy)


#untested
class AssignLargerNeighborhood(Action):

    def run(self, g: igraph.Graph):
        for i, v in enumerate(g.vs.select(in_is=True)):
            v['partition'] = i
        for v in g.vs.select(in_is=False):
            partitions = []
            for v_n in v.neighbors():
                if not v_n['partition'] is None:
                    partitions.append(v_n['partition'])
            v['partition'] = random.choice(partitions)
        del g.vs['in_is']
        return g


defined_actions.append(AssignLargerNeighborhood)


class AssignVertices(ChoiceAction):

    options = {
        'greedy': AssignGreedy,
        'larger_neighborhood': AssignLargerNeighborhood,
    }

    @staticmethod
    def default_action():
        return "greedy"


defined_actions.append(AssignVertices)
#The above actions build a partition on the graph by assigning an integer to a 'partition' attribute on each vertex
