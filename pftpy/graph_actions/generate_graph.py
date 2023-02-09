#!/usr/bin/env python3
from abc import abstractmethod
from actions import Action, ChoiceAction
import girgs_generator
from os.path import basename
import igraph

defined_actions = []
class AbstractGirg(Action):
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

        self._n = self._params['n']
        self._exec_dir = self._params['exec_dir']

        other_keys = ['n', 'exec_dir']
        girg_keys = self._params.keys() - set(other_keys)
        self._girg_dic = {k: self._params[k] for k in girg_keys}

    @staticmethod
    def default_params():
        return {
            'n': '1000',
            'exec_dir': None
        }

    def run(self, _in):
        gen = girgs_generator.generator(exec_dir=self._exec_dir)
        create_fun = self.create_graph(gen)
        graph = create_fun(self._n, **self._girg_dic)
        graph = graph.components().giant()
        self.set_stat('n', graph.vcount())
        self.set_stat('n_gen', self._n)
        self.set_stat('m', graph.ecount())

        girg_options = [f"{key}={value}" for key, value in self._girg_dic.items()]
        girg_options.sort()
        girg_options.append(f"type={self.optionname()}")
        self.set_stat('girg_options', " ".join(girg_options))

        return graph

    def get_stat_keys(self):
        keys = super().get_stat_keys()
        keys += ["girg_options"]
        keys += ["n"]
        keys += ["n_gen"]
        keys += ["m"]
        return keys

    @staticmethod
    def optionname():
        pass

    @abstractmethod
    def create_graph(self, n, **kwargs):
        pass

class HRGGen(AbstractGirg):

    @staticmethod
    def optionname():
        return "HRG"

    def create_graph(self, gen):
        return gen.create_hrg
defined_actions.append(HRGGen)

class GirgGen(AbstractGirg):

    @staticmethod
    def optionname():
        return "girg"

    def create_graph(self, gen):
        return gen.create_girg
defined_actions.append(GirgGen)

class ReadGR(Action):
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)
        self._path = self._params['path']

    @staticmethod
    def default_params():
        return {
            'path': 'graph.gr'
        }

    def run(self, _in):
        with open(self._path) as handle:
            lines: "list[str]" = [l.strip() for l in handle.readlines()]
        n, m = [int(i) for i in lines[0].split(" ")[2:]]
        edges = []
        for line in lines[1:]:
            if line.startswith("c"):
                continue
            v, w = [int(i)-1 for i in line.split(" ")]
            edge = (v, w)
            edges.append(edge)
        assert len(edges) == m
        graph = igraph.Graph(n, edges)
        self.set_stat('n', n)
        self.set_stat('m', m)
        return graph

    def get_stat_keys(self):
        return super().get_stat_keys() + ["n", "m"]
defined_actions.append(ReadGR)


class ReadEL(Action):
    """Read edge list"""
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)
        self._path = self._params['path']

    @staticmethod
    def default_params():
        return {
            'path': 'graph'
        }

    def run(self, _in):
        with open(self._path) as handle:
            lines: "list[str]" = [l.strip() for l in handle.readlines()]
        edges = []
        for line in lines[1:]:
            v, w = [int(i) for i in line.split(" ")]
            edge = (v, w)
            edges.append(edge)
        graph = igraph.Graph(edges)
        self.set_stat('n', graph.vcount())
        self.set_stat('m', graph.ecount())
        self.set_stat('graph', basename(self._path))
        return graph

    def get_stat_keys(self):
        return super().get_stat_keys() + [
            "n",
            "m",
            "graph"
        ]
defined_actions.append(ReadEL)


class GraphInput(ChoiceAction):
    options = {
        "girg": GirgGen,
        "hrg": HRGGen,
        "read": ReadGR,
        "readel": ReadEL
    }

    @staticmethod
    def default_action():
        return "hrg"


defined_actions.append(GraphInput)
