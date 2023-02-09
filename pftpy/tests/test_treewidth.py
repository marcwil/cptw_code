#!/usr/bin/env python3
import pytest
from random import shuffle
import igraph
from pftpy.actions import ActionContext
from pftpy.graph_actions import treewidth




@pytest.fixture
def tw_ctx():
    ctx = ActionContext()
    ctx.register_actions(treewidth.defined_actions)
    return ctx

def test_elimination_game_path():
    path = igraph.Graph(10, [(i, i+1) for i in range(9)])
    res, tree = treewidth.elimination_game(path, list(range(10)))
    assert res['treewidth'] == 1
    bags = [set(bag) for bag in tree.vs['vertices']]
    for i in range(9):
        assert {i, i+1} in bags


def test_elimination_game_cycle():
    cycle = igraph.Graph(10, [(i, (i+1) % 10) for i in range(10)])
    res, tree = treewidth.elimination_game(cycle, list(range(10)))
    assert res['treewidth'] == 2

def test_elimination_game_cycle_random():
    cycle = igraph.Graph(10, [(i, (i+1) % 10) for i in range(10)])
    order = list(range(10))
    for _ in range(20):
        shuffle(order)
        res, tree = treewidth.elimination_game(cycle, order)
        assert res['treewidth'] == 2
