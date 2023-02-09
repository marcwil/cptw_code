#!/usr/bin/env python3
from actions import Action, ChoiceAction
import subprocess
from tempfile import NamedTemporaryFile
import igraph

defined_actions = []

class MaxCliquesIGraph(Action):
    def run(self, graph: igraph.Graph):
        return graph.maximal_cliques()
defined_actions.append(MaxCliquesIGraph)

class QuickCliques(Action):
    def __init__(self, context, parents, parameters):
        super().__init__(context, parents, parameters)

        self.dir = self._params['dir']
        self.algo = self._params['algo']
        self.timeout = float(self._params['timeout'])

    @staticmethod
    def default_params():
        return {
            'dir': './quick-cliques/bin/',
            'algo': 'adjlist',
            'timeout': -1.0
        }

    def write_metis(self, file_handle, graph):
        file_handle.write(f"{graph.vcount()} {graph.ecount()} 1\n")
        for i in range(graph.vcount()):
            neighs = graph.neighbors(i)
            inc = [str(n+1) for n in neighs]
            file_handle.write(" ".join(inc) + "\n")
        file_handle.flush()

    def parse_output(self, stdout: str):
        lines = stdout.splitlines()
        lines = lines[2:]
        cliques = [[int(c) for c in line.split(" ")] for line in lines]
        return cliques

    def run(self, graph: igraph.Graph):
        tmp = NamedTemporaryFile(mode='w', suffix='.graph')
        self.write_metis(tmp, graph)
        command = ['./qc', f'--input-file={tmp.name}',  f'--algorithm={self.algo}']
        if self.timeout != -1.0:
            timeout_cmd = ['timeout', '-s', 'QUIT', f'{self.timeout}s']
            command = timeout_cmd + command
        proc = subprocess.run(command, cwd=self.dir, capture_output=True, text=True)
        if proc.returncode == 124:
            # timeout
            return []
        proc.check_returncode()
        res = self.parse_output(proc.stdout)
        return res
defined_actions.append(QuickCliques)

class MaximalCliques(ChoiceAction):
    options = {
        'igraph': MaxCliquesIGraph,
        'qc': QuickCliques
    }

    @staticmethod
    def default_action():
        return 'igraph'
defined_actions.append(MaximalCliques)
