#!/usr/bin/env python3
import pytest
from pftpy.actions import ActionContext
from pftpy.graph_actions import partition
import igraph

@pytest.fixture
def ctx():
    ctx = ActionContext()
    ctx.register_actions(*partition.defined_actions)
    return ctx


def test_bfpartition(ctx):
    graph: igraph.Graph = igraph.Graph.Full(4)
    a = graph.add_vertex()
    b = graph.add_vertex()
    c = graph.add_vertex()
    graph.add_edge(a, b)
    graph.add_edge(0, a)
    graph.add_edge(0, b)
    graph.add_edge(1, c)
    graph.vs['idx'] = [i for i in range(graph.vcount())]

    brute_force: partition.BFPartition = ctx.construct_action("BFPartition")
    solution, weight = brute_force.solve_rec(graph)
    print(solution)
    assert len(solution) == 3
    assert weight == 5*3*2


def test_bfpartition2(ctx):
    graph: igraph.Graph = igraph.Graph()
    a = graph.add_vertex()
    b = graph.add_vertex()
    c = graph.add_vertex()
    graph.vs['idx'] = [i for i in range(graph.vcount())]

    brute_force: partition.BFPartition = ctx.construct_action("BFPartition")
    solution, weight = brute_force.solve_rec(graph)
    print(solution)
    assert len(solution) == 3
    assert weight == 2*2*2

def test_branchingpartition(ctx):
    for i in range(10):
        graph: igraph.Graph = igraph.Graph.Erdos_Renyi(8, m=i+10)
        graph.vs['idx'] = [i for i in range(graph.vcount())]

        old_bf: partition.BFPartition = ctx.construct_action("BFPartition")

        new_bf = partition.BFPartition = ctx.construct_action("BranchingPartition")

        sol1, weight1 = old_bf.solve_rec(graph)
        sol2, weight2 = new_bf.solve_rec(graph)
        assert weight1 == weight2

def test_branchingpartition_reductions(ctx):
    for i in range(10):
        graph: igraph.Graph = igraph.Graph.Erdos_Renyi(8, m=i+10)
        graph.vs['idx'] = [i for i in range(graph.vcount())]

        bf = partition.BFPartition = ctx.construct_action("BranchingPartition")
        bf_no_lb = partition.BFPartition = ctx.construct_action("BranchingPartition")
        bf_no_lb.reduction_sw = False
        bf_no_lb.reduction_lb = False
        bf_no_lb.reduction_lb2 = False

        sol1, weight1 = bf.solve_rec(graph)
        sol2, weight2 = bf_no_lb.solve_rec(graph)
        assert weight1 == weight2
