#!/usr/bin/env python3
from io import TextIOBase
import subprocess, json
from tempfile import NamedTemporaryFile

from actions import Action, ChoiceAction

import igraph


def write_hypergraph(file: TextIOBase, n, edges):
    """
    Hypergraph format example:
    ```text
        4 2
        3 0 1 2
        2 2 3
    ```
    4 vertices, 2 edges;
    first edge has 3 vertices (0, 1, 2)
    second edge has 2 vertices (2, 3)
    """
    lines = []
    lines.append(f"{n} {len(edges)}")
    for edge in edges:
        nums = [len(edge)] + edge
        lines.append(" ".join(str(num) for num in nums))
    lines = [l + "\n" for l in lines]
    file.writelines(lines)
    file.flush()


def parse_solution(file: TextIOBase):
    return json.load(file)


defined_actions = []


class HSBranchReduce(Action):
    """
    David Stangl's Branch and Reduce solver `findminhs` for Hitting Set.

    """
    def __init__(self, context, parents, parameters):
        super().__init__(context, parents, parameters)
        self.dir = self._params['dir']
        self.timeout = int(self._params['timeout'])

    @staticmethod
    def default_params():
        return {
            'dir': './findminhs',
            'timeout': -1
        }

    def run(self, arg_in):
        """
        arg_in: tuple (n, edges), where n is the number of vertices and edges is
                a list of edges and each edge is a list of numbers between 0 and
                n-1

        returns: list of vertex IDs in solution
        """
        n, edges = arg_in
        input_fl = NamedTemporaryFile("wt")
        result_fl = NamedTemporaryFile("rt")
        settings = "./settings.json"

        write_hypergraph(input_fl.file, n, edges)

        command = [
            './target/release/findminhs',
            'solve',
            input_fl.name,
            settings,
            '-s',
            result_fl.name
        ]
        if self.timeout != -1:
            command = [
                'timeout',
                '-s',
                '15',
                f'{self.timeout}s'
            ] + command
        proc = subprocess.run(command, cwd=self.dir,
                               capture_output=True)
        if proc.returncode == 124:
            # timeout
            self.set_stat('size', -1)
            self.set_stat('status', 'timeout')
            return []
        elif proc.returncode != 0:
            # error
            self.set_stat('size', -1)
            self.set_stat('status', 'error')
        else:
            solution = json.load(result_fl.file)
            self.set_stat('size', len(solution))
            self.set_stat('status', 'success')
            return solution

    def get_stat_keys(self):
        return super().get_stat_keys() + [
            "size",
            "status"
        ]

defined_actions.append(HSBranchReduce)


def write_lp(lp_file, n, edges):
    variables = [f"x{i}" for i in range(n)]

    subject_to = []
    for i, edge in enumerate(edges):
        edge_vars = [f"x{e}" for e in edge]
        condition = f"c{i}: " + " + ".join(edge_vars) + " >= 1"
        subject_to.append(condition)

    lp_file.write("Minimize\n")
    lp_file.write("  obj: " + " + ".join(variables) + "\n")
    lp_file.write("Subject To\n")
    for condition in subject_to:
        lp_file.write("  " + condition + "\n")
    lp_file.write("Binary")
    lp_file.write("  " + " ".join(variables) + "\n")
    lp_file.write("End\n")
    lp_file.flush()

def write_lp_weighted(lp_file, weights, edges):
    n = len(weights)
    lp_file.write("Minimize\n")
    weighted_vars = [f"{float(w)} x{i}" for i,w in enumerate(weights)]
    lp_file.write("  obj: " + " + ".join(weighted_vars) + "\n")
    lp_file.write("Subject To\n")
    subject_to = []
    for i, edge in enumerate(edges):
        edge_vars = [f"x{e}" for e in edge]
        condition = f"c{i}: " + " + ".join(edge_vars) + " >= 1"
        lp_file.write("  " + condition + "\n")
    lp_file.write("Binary")
    variables = [f"x{i}" for i in range(n)]
    lp_file.write("  " + " ".join(variables) + "\n")
    lp_file.write("End\n")
    lp_file.flush()


def parse_gurobi_sol(result_file: TextIOBase):
    """
    Example gurobi output:
    ```text
        # Objective value = 5
        x 1
        y 0
        z 4
    ```
    """
    solution = []
    for line in result_file.readlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        var, val = line.split(" ")
        val = int(val)
        if val == 1:
            var_num = int(var[1:])
            solution.append(var_num)
    return solution


class GurobiHS(Action):
    def __init__(self, context, parents=None, params=None):
        super().__init__(context, parents, params)

        self.verbose = self._params['verbose']
        self.timeout = float(self._params['timeout'])

    @staticmethod
    def default_params():
        return {
            'verbose': False,
            'timeout': -1
        }

    def run(self, arg_in):
        """
        arg_in: tuple (arg1, edges), where arg1 either is the number of vertices
                or a list of vertex weights and edges is a list of edges and
                each edge is a list of numbers between 0 and n-1

        returns: list of vertex IDs in solution
        """
        arg1, edges = arg_in
        lp_file = NamedTemporaryFile("wt", suffix=".lp")
        sol_file = NamedTemporaryFile("rt", suffix=".sol")

        if isinstance(arg1, int):
            n = arg1
            write_lp(lp_file.file, n, edges)
        else:
            weights = arg1
            write_lp_weighted(lp_file.file, weights, edges)

        command = ['gurobi_cl',
                   f'ResultFile={sol_file.name}',
                   lp_file.name,
                   ]
        if self.timeout != -1:
            timeout_cmd = [
                'timeout',
                '-s',
                '3',
                f'{self.timeout}s'
            ]
            command = timeout_cmd + command

        proc = subprocess.run(
            command,
            capture_output=True,
        )

        if proc.returncode == 124:
            # timeout
            self.set_stat('status', 'timeout')
            self.set_stat('size', -1)
            return []
        elif proc.returncode != 0:
            self.set_stat('status', 'error')
            self.set_stat('size', -1)
            if self.verbose:
                print(proc)
                print(f"lp_file: {lp_file.name}")
                print(f"sol_file: {sol_file.name}")
                print(f"Out: {proc.stdout.decode('utf8')}")
                print(f"Err: {proc.stderr.decode('utf8')}")
        solution = sorted(parse_gurobi_sol(sol_file.file))
        self.set_stat('size', len(solution))
        self.set_stat('status', 'success')
        self._stdout = proc.stdout.decode('utf8')
        if self.verbose:
            print(self._stdout)
        self._stderr = proc.stderr.decode('utf8')
        return solution

    def get_stat_keys(self):
        return super().get_stat_keys() + ["size", "status"]
defined_actions.append(GurobiHS)


class HittingSet(ChoiceAction):
    options = {
        'david': HSBranchReduce,
        'gurobi': GurobiHS,
    }

    @classmethod
    def default_action(cls):
        return 'david'
defined_actions.append(HittingSet)
