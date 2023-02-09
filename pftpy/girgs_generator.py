#!/usr/bin/python3
"""Girgs generation and import into python igraph
"""
import argparse
import math
import subprocess
import tempfile
import os
from os import path
from random import randint

import igraph


def polartoxy(dist, theta=None):
    if theta is None:
        dist, theta = dist
    x = math.cos(theta) * dist
    y = math.sin(theta) * dist
    return (x,y)

class generator(object):
    def __init__(self, exec_dir=None):
        if exec_dir is None:
            exec_dir = "./girgs/build"

        self.exec_dir = exec_dir
        self.hrg_exec = path.join(self.exec_dir, "genhrg")
        self.girg_exec = path.join(self.exec_dir, "gengirg")

    def gen_girg_seeds(self, seed=None):
        res = []
        if seed is None:
            return res
        if seed == 'auto':
            seed = randint(1, 1000)
        else: #Assume seed is an integer
            seed = int(seed)
        res.append( ("wseed", seed, ) )
        res.append( ("pseed", (seed + 1) * 10, ) )
        res.append( ("sseed", (seed + 2) * 100, ) )
        return res

    def gen_hrg_seeds(self, seed=None):
        res = []
        if seed is None:
            return res
        if seed == 'auto':
            seed = randint(1, 1000)
        else: #Assume seed is an integer
            seed = int(seed)
        res.append( ("rseed", seed, ) )
        res.append( ("aseed", (seed + 1) * 10, ) )
        res.append( ("sseed", (seed + 2) * 100, ) )
        return res

    def gengirg(self, n: int, graph_file: str, seed=None, output=True, **kwargs):
        if graph_file.endswith(".txt"):
            graph_file = graph_file[:-4]  # remove .txt if present

        command = [self.girg_exec, "-n", str(n), "-edge", "1", "-file", graph_file]
        for k, v in self.gen_girg_seeds(seed):
            if k not in kwargs.keys():
                kwargs[k] = v
        for k in kwargs.keys():
            command += [f'-{k}', str(kwargs[k])]
        p = subprocess.run(command, capture_output=True, check=True, text=True)
        if output:
            print(p.stdout)


    def genhrg(self, n: int, graph_file: str, seed=None, coords=True, output=True, **kwargs):
        if graph_file.endswith(".txt"):
            graph_file = graph_file[:-4]  # remove .txt if present

        command = [self.hrg_exec, "-n", str(n), "-edge", "1", "-file", graph_file]
        if coords:
            command += ['-coord', '1']
        for k, v in self.gen_hrg_seeds(seed):
            if k not in kwargs.keys():
                kwargs[k] = v
        for k in kwargs.keys():
            command += [f'-{k}', str(kwargs[k])]
        p = subprocess.run(command, capture_output=True, check=True, text=True)
        if output:
            print(p.stdout)
    
    def parse_gargs_graph(self, fname):
        with open(fname) as handle:
            n, m = handle.readline().strip().split(" ")
            handle.readline()
            lines = [line.strip().split(" ") for line in handle]
            edges = [(int(line[0]), int(line[1])) for line in lines]
        graph = igraph.Graph(int(n), edges)
        return graph


    def create_girg(self, n, seed=None, **kwargs) -> igraph.Graph:
        txtfile = tempfile.NamedTemporaryFile(suffix=".txt")
        name = txtfile.name[:-4]

        self.gengirg(n, name, seed=seed, output=False, **kwargs)
        return self.parse_gargs_graph(txtfile.name)

    def create_hrg(self, n, seed=None, coords=False, **kwargs) -> igraph.Graph:
        txtfile = tempfile.NamedTemporaryFile(suffix=".txt")
        name = txtfile.name[:-4]

        self.genhrg(n, name, seed=seed, coords=coords, output=False, **kwargs)
        graph = self.parse_gargs_graph(txtfile.name)
        if coords:
            with open(name + '.hyp') as handle:
                lines = [line.strip().split(" ") for line in handle]
                coords = [(float(line[0]), float(line[1])) for line in lines]
                graph.vs['r'] = [c[0] for c in coords]
                graph.vs['theta'] = [c[1] for c in coords]
                coords = [polartoxy(coord) for coord in coords]
                graph.vs['x'] = [c[0] for c in coords]
                graph.vs['y'] = [c[1] for c in coords]
            os.remove(name + '.hyp')
        return graph

#gen = generator('/home/marcus/Software/girgs/build/')
#g = gen.create_hrg(1000)
